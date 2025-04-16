import pytest
from qqutils.dsutils import pget, flatten, kdict, kvdict, set_with_key


def test_set_with_key():
    assert set_with_key(['hello', 'world', 'shanghai'], len) == {'world', 'shanghai'}
    assert set_with_key(['hey', 'world', 'shanghai'], str) == {'hey', 'world', 'shanghai'}


def test_kvdict():
    assert kvdict('a', 'b', 'c') == {'a': 'a', 'b': 'b', 'c': 'c'}


@pytest.mark.skip(reason="Can't be tested in pytest: AssertionError: should not be invoked in a REPL")
def test_kdict():
    a, b, c = 1, 2, 3
    assert kdict(a, b, c) == {'a': 1, 'b': 2, 'c': 3}


def test_flatten():
    assert list(flatten([1, 2, 3])) == [1, 2, 3]
    assert list(flatten((1, 2, 3))) == [1, 2, 3]
    assert list(flatten({1, 2, 3})) == [1, 2, 3]

    assert list(flatten([1, 2, [3, 4], 5])) == [1, 2, 3, 4, 5]
    assert list(flatten([1, 2, (3, 4), 5])) == [1, 2, 3, 4, 5]
    assert list(flatten([1, 2, {3, 4}, 5])) == [1, 2, 3, 4, 5]
    assert list(flatten([1, 2, [3, 4], 5], as_list=True)) == [1, 2, 3, 4, 5]
    assert list(flatten([1, 2, (3, 4), 5], as_list=True)) == [1, 2, 3, 4, 5]
    assert list(flatten([1, 2, {3, 4}, 5], as_list=True)) == [1, 2, 3, 4, 5]


def test_pget():
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
    assert pget(data, 'a.b.e') is None
    assert pget(data, 'a.b.e', 'n/a') == 'n/a'
    assert pget(data, 'a.b.e', 12) == 12
    assert pget(data, 'a.b.d[0].e') == 1
    assert pget(data, 'a.b.d[1].f') == 2
    assert pget(data, 'a.b.d[2].f') is None
    assert pget(data, 'a.b.d[-1].f') == 2
    assert pget(data, 'a.b.g[1]') is None
    assert pget(data, 'a.b.g[2]', 'n/a') == 'n/a'
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
