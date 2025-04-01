from qqutils.osutils import (
    from_path_str,
)


def test_from_path_str():
    p = from_path_str('/var/log')
    print(p.as_posix())
