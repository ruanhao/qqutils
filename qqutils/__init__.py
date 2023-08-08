from hprint import hprint
from functools import partial, wraps
from icecream import Source
import inspect
import traceback
import logging


__all__ = [
    # PRINT UTILS
    'hprint',

    # SETUP UTILS
    'install_print_with_flush',

    # DATASCTRUCTURE MANIPULATION UTILS
    'chain_get',
    'flatten',
    'kvdict',
    'kdict',

    # EXCEPTION UTILS
    'sneaky'
]



def install_print_with_flush():
    try:
        builtins = __import__('__builtin__')
    except ImportError:
        builtins = __import__('builtins')

    setattr(builtins, 'print0', print)
    setattr(builtins, 'print', partial(print, flush=True))


def chain_get(data, chain, default=None):
    attrs = chain.split('.')
    if len(attrs) == 1:
        return data.get(attrs[0], default)
    result = data
    for attr in attrs[:-1]:
        result = result.get(attr, {})
    return result.get(attrs[-1], default)


def _flatten(L):
    if not isinstance(L, (list, tuple, set)):
        yield L
        return
    for F in L:
        yield from flatten(F)


def flatten(L):
    return list(_flatten(L))


def kdict(*args, **kwargs):
    """
    create dict only by key

    > a, b, c = 1, 2, 3
    > d = kdict(a, b, c)
    > d
    > {'a': 1, 'b': 2, 'c': 3}

    """
    assert not kwargs, "kwargs not allowed"
    callFrame = inspect.currentframe().f_back
    callNode = Source.executing(callFrame).node
    assert callNode, "should not be invoked in a REPL"
    source = Source.for_frame(callFrame)
    tokens = source.asttokens()
    argStrs = [
        tokens.get_text(node)
        for node in callNode.args
    ]
    return dict(zip(argStrs, args))


def kvdict(*lst):
    """
    >>> kvdict('a', 'b', 'c')
    {'a': 'a', 'b': 'b', 'c': 'c'}
    """
    return dict(list(zip(lst, lst)))


def sneaky(logger=None):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kw):
            try:
                return func(*args, **kw)
            except Exception as e:
                tb = traceback.format_exc()
                if logger:
                    logger.error("%s: \n%s", e, str(tb))
        return wrapper
    return decorate
