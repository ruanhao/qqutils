import os
import sys
import ssl
import json
import socket
import select
import pickle
import base64
import asyncio
import logging
import requests
from pathlib import Path
from attrs import define, field
from contextlib import contextmanager
from functools import partial, lru_cache
from .funcutils import cached
from .osutils import from_module
from .threadutils import submit_daemon_thread
from .logutils import pdebug, pinfo, perror, sneaky
from typing import Tuple, Callable, Mapping, Awaitable, TYPE_CHECKING, Union

if TYPE_CHECKING:
    import httpx

__all__ = (
    'disable_urllib3_warnings',
    'download',
    'upload_multipart',
    'check_http_response',
    'http_get',
    'http_post',
    'http_put',
    'http_delete',
    'http_patch',
    'http_session_get',
    'http_session_post',
    'http_session_put',
    'http_session_delete',
    'http_session_patch',

    'httpx_get',
    'httpx_post',
    'httpx_put',
    'httpx_delete',
    'httpx_patch',
    'httpx_session_get',
    'httpx_session_post',
    'httpx_session_put',
    'httpx_session_delete',
    'httpx_session_patch',

    'encode_session_base64',
    'decode_session_base64',
    'sockinfo',
    'run_proxy',
    'sendall',
    'recvall',
    'acceptall',
    'eventfd',
    'sock_connect',
    'is_readable',
    'is_port_in_use',
    'run_proxy_async',
)

logger = logging.getLogger(__name__)


def disable_urllib3_warnings():
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def check_http_response(response: Union[requests.Response, 'httpx.Response'], need_raise: bool = True) -> None:
    import httpx
    try:
        response.raise_for_status()
    except (requests.HTTPError, httpx.HTTPStatusError):
        if 'application/json' in (response.headers.get('content-type') or ''):
            print(json.dumps(response.json(), indent=4), file=sys.stderr)
        else:
            if response.text:
                print(response.text, file=sys.stderr)
        if need_raise:
            raise


@lru_cache(maxsize=8)
def __http_adapter(retries=2):
    from requests.adapters import HTTPAdapter
    return HTTPAdapter(max_retries=retries)


@lru_cache(maxsize=8)
def __httpx_mounts(retries=1) -> Mapping[str, 'httpx.AsyncHTTPTransport']:
    import httpx
    transport = httpx.AsyncHTTPTransport(verify=False, retries=retries)
    return {
        'http://': transport,
        'https://': transport
    }


def _http_method(url, method, session=None, check=True, *args, **kwargs):
    method = (method or '').lower()
    assert method in ['get', 'post', 'delete', 'put', 'patch']
    s = session or requests.Session()
    s.mount('http://', __http_adapter())
    s.mount('https://', __http_adapter())
    s.verify = False
    logger.debug(f'{method.upper()} {url}, args: {args}, kwargs: {kwargs}')
    response = getattr(s, method)(url, *args, **kwargs)
    response.encoding = response.apparent_encoding
    if check:
        check_http_response(response)
    return response


http_get = partial(_http_method, method='get')
http_post = partial(_http_method, method='post')
http_put = partial(_http_method, method='put')
http_delete = partial(_http_method, method='delete')
http_patch = partial(_http_method, method='patch')


def http_session_get(session, url, *args, **kwargs):
    return _http_method(url, 'get', session, *args, **kwargs)


def http_session_post(session, url, *args, **kwargs):
    return _http_method(url, 'post', session, *args, **kwargs)


def http_session_put(session, url, *args, **kwargs):
    return _http_method(url, 'put', session, *args, **kwargs)


def http_session_delete(session, url, *args, **kwargs):
    return _http_method(url, 'delete', session, *args, **kwargs)


def http_session_patch(session, url, *args, **kwargs):
    return _http_method(url, 'patch', session, *args, **kwargs)


# httpx

async def _httpx_method(url: str, method: str, session: 'httpx.AsyncClient' = None, check: bool = True, *args, **kwargs) -> Awaitable['httpx.Response']:
    import httpx
    from charset_normalizer import from_bytes
    method = (method or '').lower()
    assert method in ['get', 'post', 'delete', 'put', 'patch']
    s = session or httpx.AsyncClient(mounts=__httpx_mounts())
    logger.debug(f"{method.upper()} {url}, args: {args}, kwargs: {kwargs}")
    response: httpx.Response = await getattr(s, method)(url, *args, **kwargs)
    detected = from_bytes(response.content).best()
    if detected:
        response.encoding = detected.encoding
    if check:
        check_http_response(response)
    return response


httpx_get: Callable[..., Awaitable['httpx.Response']] = partial(_httpx_method, method='get')
httpx_post: Callable[..., Awaitable['httpx.Response']] = partial(_httpx_method, method='post')
httpx_put: Callable[..., Awaitable['httpx.Response']] = partial(_httpx_method, method='put')
httpx_delete: Callable[..., Awaitable['httpx.Response']] = partial(_httpx_method, method='delete')
httpx_patch: Callable[..., Awaitable['httpx.Response']] = partial(_httpx_method, method='patch')


async def httpx_session_get(session: 'httpx.AsyncClient', url: str, *args, **kwargs) -> Awaitable['httpx.Response']:
    return await _http_method(url, 'get', session, *args, **kwargs)


async def httpx_session_post(session: 'httpx.AsyncClient', url: str, *args, **kwargs) -> Awaitable['httpx.Response']:
    return await _http_method(url, 'post', session, *args, **kwargs)


async def httpx_session_put(session: 'httpx.AsyncClient', url: str, *args, **kwargs) -> Awaitable['httpx.Response']:
    return await _http_method(url, 'put', session, *args, **kwargs)


async def httpx_session_delete(session: 'httpx.AsyncClient', url: str, *args, **kwargs) -> Awaitable['httpx.Response']:
    return await _http_method(url, 'delete', session, *args, **kwargs)


async def httpx_session_patch(session: 'httpx.AsyncClient', url: str, *args, **kwargs) -> Awaitable['httpx.Response']:
    return await _http_method(url, 'patch', session, *args, **kwargs)


def encode_session_base64(session: requests.Session) -> str:
    return base64.b64encode(pickle.dumps(session)).decode()


def decode_session_base64(text: str) -> requests.Session:
    return pickle.loads(base64.b64decode(text.encode()))


def is_readable(sock: socket.socket) -> bool:
    try:
        # this will try to read bytes without blocking and also without removing them from buffer (peek only)
        return not sock.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK) == b''
    except Exception:
        return False


def _handle(buffer, direction, src, dst):
    # codecs.register_error('using_dot', lambda e: ('.', e.start + 1))
    # click.secho(buffer.decode('ascii', errors='using_dot'), fg='green' if direction else 'yellow')
    return buffer


def socket_description(sock):
    """[id: 0xd829bade, L:/127.0.0.1:2069 - R:/127.0.0.1:55666]"""
    sock_id = hex(id(sock))
    fileno = sock.fileno()
    s_addr = None
    try:
        s_addr, s_port = sock.getsockname()[:2]
        d_addr, d_port = sock.getpeername()[:2]
        return f"[id: {sock_id}, fd: {fileno}, L:/{s_addr}:{s_port} - R:/{d_addr}:{d_port}]"
    except Exception:
        if s_addr:
            return f"[id: {sock_id}, fd: {fileno}, LISTENING]"
        else:
            return f"[id: {sock_id}, fd: {fileno}, CLOSED]"


sockinfo = socket_description


def sock_connect(address, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((address, port))
    return sock


@contextmanager
def _preserve_blocking_mode(sock):
    origin_blocking = sock.getblocking()
    if origin_blocking:
        sock.setblocking(0)
    try:
        yield sock
    finally:
        if origin_blocking:
            sock.setblocking(origin_blocking)


def acceptall(sock: socket.socket) -> list:
    result = []
    with _preserve_blocking_mode(sock):
        while True:
            try:
                result.append(sock.accept())
            except socket.error:
                return result


def recvall(sock: socket.socket, timeout=0) -> bytes:
    """if timeout is non-zero, it will block at the first time"""
    buffer = b''
    with _preserve_blocking_mode(sock):
        while True:
            if select.select([sock], [], [], timeout):
                try:
                    received = sock.recv(1024)
                    if not received:  # EOF
                        return buffer
                    buffer += received
                    timeout = 0
                except socket.error:
                    return buffer
            else:               # timeout
                return buffer


# return the remaining buffer
def sendall(sock: socket.socket, buffer: bytes, spin: int = 2) -> bytes:
    total_sent = 0
    with _preserve_blocking_mode(sock):
        while total_sent < len(buffer):
            try:
                total_sent += sock.send(buffer[total_sent:])
                # print(f"Totally {total_sent/1024} K sent [{round(total_sent / len(buffer) * 100, 2)}%]\r", end='')
            except socket.error:
                if spin > 0:
                    spin -= 1
                    continue
                break
        return buffer[total_sent:]


@sneaky(logger)
def _transfer(src, dst, direction, handle):
    src_address, src_port = src.getsockname()
    src_peer_address, src_peer_port = src.getpeername()
    dst_address, dst_port = dst.getsockname()
    dst_peer_address, dst_peer_port = dst.getpeername()
    try:
        while True:
            buffer = src.recv(4096)
            if len(buffer) > 0:
                if direction:
                    pdebug(f"[>> {len(buffer)} bytes] {src_peer_address, src_peer_port} >> {dst_address, dst_port}")
                else:
                    pdebug(f"[<< {len(buffer)} bytes] {dst_peer_address, dst_peer_port} << {src_address, src_port}")
                sendall(dst, handle(buffer, direction, src, dst))
            else:    # EOF
                handle(buffer, direction, src, dst)
                return
    except socket.error:
        return
    finally:
        if direction:
            pdebug(f"[Inactive] {src_peer_address, src_peer_port}")
        else:
            pdebug(f"[Inactive] {src_address, src_port}")
        src.close()
        if not dst._closed:
            dst.close()


@cached
def _c_context():
    ssl_context = ssl._create_unverified_context()
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.set_ciphers("ALL")
    return ssl_context


@cached
def _s_context():
    s_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    certfile = from_module('cert-qqutils.pem')
    keyfile = from_module('key-qqutils.pem')
    s_context.load_cert_chain(certfile, keyfile)
    return s_context


@define(slots=True)
class _Socket:
    peername: Tuple[str, int] = field(default=None)

    def getpeername(self):
        return self.peername


@define(slots=True, kw_only=True)
class _ProxyServer:
    host: str = field(default='localhost')
    port: int = field(default=8080)
    remote_host: str = field(default='localhost')
    remote_port: int = field(default=80)
    certfile: str = field(default=None)
    keyfile: str = field(default=None)
    tls: bool = field(default=False)  # if True, proxy client will connect to real server with TLS
    handle: Callable = field(default=_handle)

    def ssl_context(self, certfile, keyfile):
        if all((certfile, keyfile)):
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile, keyfile)
            return context
        elif any((certfile, keyfile)):
            raise ValueError("Both certfile and keyfile are required")
        else:
            return None

    async def transfer(
            self,
            reader: asyncio.streams.StreamReader,
            writer: asyncio.streams.StreamWriter,
            source_writer: asyncio.streams.StreamWriter,
            direction=False, handle=_handle
    ):
        spname = source_writer.get_extra_info('peername')
        src_address, src_port = spname[0], spname[1]
        ssockname = source_writer.get_extra_info('sockname')
        src_peer_address, src_peer_port = ssockname[0], ssockname[1]

        dsockname = writer.get_extra_info('sockname')
        dst_address, dst_port = dsockname[0], dsockname[1]
        dpname = writer.get_extra_info('peername')
        dst_peer_address, dst_peer_port = dpname[0], dpname[1]

        try:
            while True:
                buffer = await reader.read(4096)
                if len(buffer) > 0:
                    if direction:
                        pdebug(f"[>> {len(buffer)} bytes] {src_peer_address, src_peer_port} >> {dst_address, dst_port}")
                    else:
                        pdebug(f"[<< {len(buffer)} bytes] {dst_peer_address, dst_peer_port} << {src_address, src_port}")
                    src = _Socket((src_address, src_port))
                    dst = _Socket((dst_peer_address, dst_peer_port))
                    writer.write(handle(buffer, direction, src, dst))
                    await writer.drain()
                else:    # EOF
                    handle(buffer, direction, src, dst)
                    return
        except Exception:
            return
        finally:
            if direction:
                pdebug(f"[Inactive] {src_peer_address, src_peer_port}")
            else:
                pdebug(f"[Inactive] {src_address, src_port}")
            writer.close()

    async def handle_incoming_connection(self, reader: asyncio.streams.StreamReader, writer: asyncio.streams.StreamWriter):
        address = writer.get_extra_info('peername')
        logger.info(f"New connection from {address}")
        p_reader, p_writer = await asyncio.open_connection(self.remote_host, self.remote_port, ssl=_c_context() if self.tls else None)
        asyncio.create_task(self.transfer(reader, p_writer, writer, True, self.handle))
        asyncio.create_task(self.transfer(p_reader, writer, p_writer, False, self.handle))

    async def run(self):
        server = await asyncio.start_server(
            self.handle_incoming_connection,
            self.host, self.port,
            reuse_address=True,
            ssl=self.ssl_context(self.certfile, self.keyfile)
        )
        tls = all((self.certfile, self.keyfile))
        logger.info(f"Server started at {self.host}:{self.port} ({'secure' if tls else 'plain'}) ...")
        async with server:
            await server.serve_forever()


def run_proxy_async(
        local_host, local_port,
        remote_host, remote_port,
        handle=_handle,
        tls=False,              # client side
        server_keyfile=None, server_certfile=None,  # server side
):

    asyncio.run(_ProxyServer(
        host=local_host, port=local_port,
        remote_host=remote_host, remote_port=remote_port,
        certfile=server_certfile, keyfile=server_keyfile,
        tls=tls,
        handle=handle,
    ).run())


def run_proxy(
        local_host, local_port,
        remote_host, remote_port,
        handle=_handle,
        tls=False, tls_server=False
):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((local_host, local_port))
    server_socket.listen()
    if tls_server:
        server_socket = _s_context().wrap_socket(server_socket, server_side=True)
    transfer = partial(_transfer, handle=handle or _handle)
    pinfo(f"Proxy server started listening: ({local_host}:{local_port}){'(TLS)' if tls_server else ''} => ({remote_host}:{remote_port}){'(TLS)' if tls else ''} ...")
    while True:
        try:
            src_socket, src_address = server_socket.accept()
        except socket.error:
            continue
        pdebug(f"[Establishing] {src_address} <=> {server_socket.getsockname()} <-> ?")
        try:
            dst_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if tls:
                dst_socket = _c_context().wrap_socket(dst_socket, server_hostname=remote_host)
            dst_socket.connect((remote_host, remote_port))
            pdebug(f"[Established ] {src_address} <=> {src_socket.getsockname()} <-> {socket_description(dst_socket)}")
            submit_daemon_thread(transfer, dst_socket, src_socket, False)
            submit_daemon_thread(transfer, src_socket, dst_socket, True)
        except Exception as e:
            perror(repr(e))


class BaseEventFD(object):
    """Class implementing event objects that has a fd that can be selected.

    This EventFD class implements the same functions as a regular Event but it
    has a file descriptor. The file descriptor can be accessed using the fileno function.
    This event can be passed to select, poll and it will block until the event will be set.

    Reference: https://github.com/palaviv/eventfd/blob/develop/eventfd/_eventfd.py
    """

    _DATA = None

    def __init__(self):
        self._flag = False
        self._read_fd = None
        self._write_fd = None

    def _read(self, len):
        return os.read(self._read_fd, len)

    def _write(self, data):
        os.write(self._write_fd, data)

    def is_set(self):
        """Return true if and only if the internal flag is true."""
        return self._flag

    def clear(self):
        """Reset the internal flag to false.

        Subsequently, threads calling wait() will block until set() is called to
        set the internal flag to true again.

        """
        if self._flag:
            self._flag = False
            assert self._read(len(self._DATA)) == self._DATA

    def unsafe_write(self):
        self._write(self._DATA)

    def unsafe_read(self):
        self._read(len(self._DATA))

    def set(self):
        """Set the internal flag to true.

        All threads waiting for it to become true are awakened. Threads
        that call wait() once the flag is true will not block at all.

        """
        if not self._flag:
            self._flag = True
            self._write(self._DATA)

    def wait(self, timeout=None):
        """Block until the internal flag is true.

        If the internal flag is true on entry, return immediately. Otherwise,
        block until another thread calls set() to set the flag to true, or until
        the optional timeout occurs.

        When the timeout argument is present and not None, it should be a
        floating point number specifying a timeout for the operation in seconds
        (or fractions thereof).

        This method returns the internal flag on exit, so it will always return
        True except if a timeout is given and the operation times out.

        """
        if not self._flag:
            ret = select.select([self], [], [], timeout)
            assert ret[0] in [[self], []]
        return self._flag

    def fileno(self):
        """Return a file descriptor that can be selected.

        You should not use this directly pass the EventFD object instead.

        Reference: https://docs.python.org/3/library/select.html#select.select
        """
        return self._read_fd

    def __del__(self):
        """Closes the file descriptors"""
        raise NotImplementedError


class PipeEventFD(BaseEventFD):

    _DATA = b"A"

    def __init__(self):
        super(PipeEventFD, self).__init__()
        self._read_fd, self._write_fd = os.pipe()

    def __del__(self):
        os.close(self._read_fd)
        os.close(self._write_fd)


class SocketEventFD(BaseEventFD):

    _DATA = b'A'

    def __init__(self):
        super(SocketEventFD, self).__init__()
        temp_fd = socket.socket()
        temp_fd.bind(("127.0.0.1", 0))
        temp_fd.listen(1)
        self._read_fd = socket.create_connection(temp_fd.getsockname())
        self._write_fd, _ = temp_fd.accept()
        temp_fd.close()

    def _read(self, len):
        return self._read_fd.recv(len)

    def _write(self, data):
        self._write_fd.send(data)

    def fileno(self):
        return self._read_fd.fileno()

    def __del__(self):
        self._read_fd.close()
        self._write_fd.close()


def eventfd():
    if os.name != "nt":         # Linux
        return PipeEventFD()
    else:                       # Windows
        return SocketEventFD()


def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def upload_multipart(url: str, path: Path, name='file', progress: bool = False, session: requests.Session = None):
    from requests_toolbelt.multipart import encoder
    file_size = path.stat().st_size
    filename = path.name
    headers0 = {
        # 'Accept-Language': 'zh-CN,zh;q=0.9',  # https://www.cnblogs.com/liuxiaoming123/p/15315868.html
    }
    session = session or requests.Session()
    if not progress:
        with path.open("rb") as f:
            multipart_encoder = encoder.MultipartEncoder(
                fields={
                    # name: (filename, f, 'application/macbinary')
                    name: (filename, f)
                },
            )
            headers = {
                'Content-Type': multipart_encoder.content_type,
                **headers0,
            }
            return session.post(url, data=multipart_encoder, headers=headers)

    with path.open("rb") as f:
        from tqdm import tqdm
        from tqdm.utils import CallbackIOWrapper
        with tqdm(total=file_size, unit="B", unit_scale=True, unit_divisor=1024) as t:
            wrapped_file = CallbackIOWrapper(t.update, f, "read")
            multipart_encoder = encoder.MultipartEncoder(
                fields={
                    # name: (filename, wrapped_file, 'application/macbinary')
                    name: (filename, wrapped_file)
                },
            )
            monitor = encoder.MultipartEncoderMonitor(multipart_encoder)
            headers = {
                'Content-Type': multipart_encoder.content_type,
                **headers0,
            }
            return session.post(url, data=monitor, headers=headers)


def download(url: str, path: Path, chunk_size: int = 1024, progress: bool = False):
    r = requests.get(url, stream=True)
    total = int(r.headers.get('content-length', 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    if not progress:
        with path.open('wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        return
    from tqdm import tqdm
    with tqdm(total=total, unit='B', unit_scale=True, unit_divisor=1024) as bar:
        with path.open('wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))
