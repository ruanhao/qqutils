from functools import wraps


def cached(func):
    obj = None

    @wraps(func)
    def inner(*args, **kwargs):
        nonlocal obj
        if obj is None:
            obj = func(*args, **kwargs)
        return obj
    return inner
