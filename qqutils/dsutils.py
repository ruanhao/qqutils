from icecream import Source
import inspect


def _chain_get(data, chain, default=None):
    attrs = chain.split('.')
    if len(attrs) == 1:
        return data.get(attrs[0], default)
    result = data
    for attr in attrs[:-1]:
        result = result.get(attr, {})
    return result.get(attrs[-1], default)


def pget(obj, key, default='n/a'):
    try:
        return _chain_get(obj, key, default)
    except Exception:
        return default


def _flatten(L):
    if not isinstance(L, (list, tuple, set)):
        yield L
        return
    for F in L:
        yield from flatten(F)


def flatten(L, as_list=False):
    return list(_flatten(L)) if as_list else _flatten(L)


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


def set_with_key(iterable, key):
    """>>> set_with_key(['hello', 'world', 'shanghai'], len)
{'world', 'shanghai'}
>>> set_with_key(['hey', 'world', 'shanghai'], len)
{'hey', 'world', 'shanghai'}"""
    return set({key(i): i for i in iterable}.values())
