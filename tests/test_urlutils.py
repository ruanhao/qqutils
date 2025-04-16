from qqutils.urlutils import get_param


def test_get_param():
    url = "https://example.com/path?param1=value1&param2=value2"
    assert get_param(url, "param1") == "value1"
    assert get_param(url, "param2") == "value2"
    assert get_param(url, "param3") is None
