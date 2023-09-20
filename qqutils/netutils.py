import requests
from functools import partial
import sys
import json
import socket
import ssl
import traceback
import select
import os
from .funcutils import cached
from .logutils import pdebug, pinfo, perror, sneaky
from .threadutils import submit_thread
from .osutils import from_module
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def check_http_response(response, need_raise=True):
    if response.ok:
        return
    if 'application/json' in response.headers.get('content-type'):
        print(json.dumps(response.json(), indent=4), file=sys.stderr)
    else:
        print(response.text, file=sys.stderr)
    if need_raise:
        response.raise_for_status()


def _http_method(url, method, *args, **kwargs):
    assert method in ['get', 'post', 'delete', 'put']
    response = getattr(requests, method)(url, *args, **kwargs)
    check_http_response(response)
    return response


http_get = partial(_http_method, method='get')
http_post = partial(_http_method, method='post')
http_put = partial(_http_method, method='put')
http_delete = partial(_http_method, method='delete')


def is_socket_closed(sock: socket.socket) -> bool:
    try:
        # this will try to read bytes without blocking and also without removing them from buffer (peek only)
        data = sock.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
        if len(data) == 0:
            return True
    except BlockingIOError:
        return False  # socket is open and reading from it would block
    except ConnectionResetError:
        return True  # socket was closed for some other reason
    except Exception:
        return False
    return False


def _handle(buffer, direction, src, dst):
    # codecs.register_error('using_dot', lambda e: ('.', e.start + 1))
    # click.secho(buffer.decode('ascii', errors='using_dot'), fg='green' if direction else 'yellow')
    return buffer


def socket_description(sock):
    return f"{sock.getsockname()} <=> {sock.getpeername()}"

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
