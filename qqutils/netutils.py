import sys
import os
import ssl
import json
import socket
import select
import logging
import requests
import pickle
import base64
from pathlib import Path
from qqutils.funcutils import cached
from qqutils.osutils import from_module
from contextlib import contextmanager
from qqutils.threadutils import submit_thread
from functools import partial, lru_cache
from requests.adapters import HTTPAdapter
from qqutils.logutils import pdebug, pinfo, perror, sneaky
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper
from requests_toolbelt.multipart import encoder

logger = logging.getLogger(__name__)


def check_http_response(response, need_raise=True):
    if response.ok:
        return
    if 'application/json' in (response.headers.get('content-type') or ''):
        print(json.dumps(response.json(), indent=4), file=sys.stderr)
    else:
        print(response.text, file=sys.stderr)
    if need_raise:
        response.raise_for_status()


@lru_cache(maxsize=8)
def __http_adapter(retries=2):
    return HTTPAdapter(max_retries=retries)


def _http_method(url, method, session=None, *args, **kwargs):
    assert method in ['get', 'post', 'delete', 'put']
    s = session or requests.Session()
    s.mount('http://', __http_adapter())
    s.mount('https://', __http_adapter())
    response = getattr(s, method)(url, *args, **kwargs)
    response.encoding = response.apparent_encoding
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
    '''[id: 0xd829bade, L:/127.0.0.1:2069 - R:/127.0.0.1:55666]'''
    sock_id = hex(id(sock))
    fileno = sock.fileno()
    s_addr = None
    try:
        s_addr, s_port = sock.getsockname()
        d_addr, d_port = sock.getpeername()
        return f"[id: {sock_id}, fd: {fileno}, L:/{s_addr}:{s_port} - R:/{d_addr}:{d_port}]"
        pass
    except Exception:
        if s_addr:
            return f"[id: {sock_id}, fd: {fileno}, LISTENING]"
        else:
            return f"[id: {sock_id}, fd: {fileno}, CLOSED]"

    return f"{sock.getsockname()} <=> {sock.getpeername()}"


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
    return ssl._create_unverified_context()


@cached
def _s_context():
    s_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    certfile = from_module('cert-qqutils.pem')
    keyfile = from_module('key-qqutils.pem')
    s_context.load_cert_chain(certfile, keyfile)
    return s_context


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
            submit_thread(transfer, dst_socket, src_socket, False)
            submit_thread(transfer, src_socket, dst_socket, True)
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
    with tqdm(total=total, unit='B', unit_scale=True, unit_divisor=1024) as bar:
        with path.open('wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))


def backup(path: Path, suffix: str = '.bak', force: bool = False):
    if not path.exists():
        return
    bak_path = path.with_suffix(suffix)
    if bak_path.exists() and not force:
        return
    with path.open('rb') as source:
        with bak_path.open('wb') as target:
            target.write(source.read())


def _test_upload_multipart():
    # r = upload_multipart("https://httpbin.org/post", Path("dbgutils.py"))
    r = upload_multipart("http://localhost:8080/post", Path("dbgutils.py"))
    assert r.ok, r.text
    print(r.text)


if __name__ == '__main__':
    _test_upload_multipart()
