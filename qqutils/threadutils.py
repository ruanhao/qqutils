from concurrent.futures import ThreadPoolExecutor


def _create_thread_pool(max_workers=64, thread_name_prefix="qThreadPoolExecutor"):
    return ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=thread_name_prefix)


_POOL = _create_thread_pool()


def submit_thread(func, *args, **kwargs):
    return _POOL.submit(func, *args, **kwargs)


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
    _POOL = _create_thread_pool()
