import requests
from functools import partial
import sys
import json
import socket
import ssl
from .funcutils import cached
from .logutils import pdebug, pinfo, perror
from .threadutils import submit_thread
from .osutils import from_module
import traceback


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


def _transfer(src, dst, direction, handle):
    src_address, src_port = src.getsockname()
    src_peer_address, src_peer_port = src.getpeername()
    dst_address, dst_port = dst.getsockname()
    dst_peer_address, dst_peer_port = dst.getpeername()
    while True:
        try:
            buffer = src.recv(4096)
            if len(buffer) > 0:
                if direction:
                    pdebug(f"[>> {len(buffer)} bytes] {src_peer_address, src_peer_port} >> {dst_address, dst_port}")
                else:
                    pdebug(f"[<< {len(buffer)} bytes] {dst_peer_address, dst_peer_port} << {src_address, src_port}")
                dst.send(handle(buffer, direction, src, dst))
            else:    # len(buffer) == 0
                if direction:
                    pdebug(f"[Inactive] {src_peer_address, src_peer_port}")
                else:
                    pdebug(f"[Inactive] {src_address, src_port}")
                src.close()
                if not dst._closed:
                    dst.close()
                return
        except Exception:
            tb = traceback.format_exc()
            perror(f"[Exception] {tb}")
            src.close()
            dst.close()
            return


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
        src_socket, src_address = server_socket.accept()
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
