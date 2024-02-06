from icecream import Source
from typing import Any, Dict, List, Union
import inspect


def _get(data, key, default=None):
    if '[' not in key:
        assert ']' not in key, "invalid key: %s" % key
        return data.get(key, default)
    else:
        assert ']' in key, "invalid key: %s" % key
        idx0 = key.index('[')
        idx1 = key.index(']')
        assert idx0 < idx1, "invalid key: %s" % key
        idx = int(key[idx0 + 1:idx1])
        key = key[:idx0]
        if not key:             # data = [{'a': 1}, {'a': 2}, {'a': 3}]; pget(data, '[0].a')
            lst = data
        else:
            lst = data.get(key, [])
        if lst is None:
            return default
        assert isinstance(lst, (list, tuple)), "invalid key (should be list or tuple): %s" % key
        if lst:
            return lst[idx]
        else:
            return default


def _chain_get(data, chain, default=None):
    attrs = chain.split('.')
    if len(attrs) == 1:
        return _get(data, attrs[0], default)
    result = data
    for attr in attrs[:-1]:
        result = _get(result, attr, {})
    return _get(result, attrs[-1], default)


def pget(obj: Union[List, Dict], key: str, default: Any = 'n/a'):
    try:
        return _chain_get(obj, key, default)
    except AssertionError as ae:
        raise ValueError(str(ae))
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


def _test_pget():
    data = {
        'a': {
            'b': {
                'c': 1,
                'd': [
                    {
                        'e': 1
                    },
                    {
                        'f': 2
                    }
                ],
                'g': None
            }
        }
    }
    data2 = [
        {
            'a': 1
        }
    ]
    assert pget(data, 'a.b.c') == 1
    assert pget(data, 'a.b.e') == 'n/a'
    assert pget(data, 'a.b.e', None) is None
    assert pget(data, 'a.b.e', 12) == 12
    assert pget(data, 'a.b.d[0].e') == 1
    assert pget(data, 'a.b.d[1].f') == 2
    assert pget(data, 'a.b.d[2].f') == 'n/a'
    assert pget(data, 'a.b.d[-1].f') == 2
    assert pget(data, 'a.b.g[1]') == 'n/a'
    assert pget(data, 'a.b.g') is None
    try:
        pget(data, 'a.b.d[2.f')
        assert False, "should raise exception"
    except Exception:
        pass
    try:
        pget(data, 'a.b.d2].f')
        assert False, "should raise exception"
    except Exception:
        pass
    try:
        pget(data, 'a.b.][d2.f')
        assert False, "should raise exception"
    except Exception:
        pass

    assert pget(data2, '[0].a') == 1


if __name__ == '__main__':
    _test_pget()
