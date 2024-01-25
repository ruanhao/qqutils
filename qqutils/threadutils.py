import itertools
import threading
from concurrent.futures import ThreadPoolExecutor


_counter = itertools.count()


def create_thread_pool(n=None, prefix=''):
    return ThreadPoolExecutor(max_workers=n, thread_name_prefix=prefix or f'ThreadPool-{next(_counter)}')


_POOL = create_thread_pool()


def submit_thread(func, *args, **kwargs):
    return _POOL.submit(func, *args, **kwargs)


def submit_daemon_thread(func, *args, **kwargs) -> threading.Thread:
    func_name = func.__name__

    def _worker():
        func(*args, **kwargs)

    t = threading.Thread(target=_worker, name=f'{func_name}-daemon-{next(_counter)}', daemon=True)
    t.start()
    return t


def submit_thread_and_wait(func, *args, **kwargs):
    return _POOL.submit(func, *args, **kwargs).result()


def submit_thread_and_wait_with_timeout(timeout, func, *args, **kwargs):
    return _POOL.submit(func, *args, **kwargs).result(timeout)


def submit_thread_with_callback(cb, func, *args, **kwargs):
    f = _POOL.submit(func, *args, **kwargs)

    def __cb(future):
        cb(future.result())
    f.add_done_callback(__cb)
    return f


def wait_forever():
    global _POOL
    _POOL.shutdown(wait=True)
    _POOL = create_thread_pool()
