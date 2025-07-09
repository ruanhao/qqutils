import os
import getpass
from qqutils.osutils import (
    from_module,
    from_path_str,
    temp_dir,
    under_home,
)
from qqutils.dateutils import timestamp_millis


def test_temp_dir():
    p = temp_dir().as_posix()
    assert "/tmp" in p or "/var/tmp" in p or "Temp" in p
    p = temp_dir(mkdtemp=True).as_posix()
    assert "/tmp/" in p


def test_from_path_str():
    p = from_path_str('/var/log')
    assert "/var/log" in p.as_posix()


def test_under_home():
    username = getpass.getuser()
    filename = f"test_{timestamp_millis()}.txt"
    p = under_home("qqutils_test", "subdir", filename)
    assert username in p.as_posix()
    assert not p.exists()

    filename = f"test_{timestamp_millis()}.txt"
    p = under_home("qqutils_test", "subdir", filename, create=True)
    assert username in p.as_posix()
    assert p.exists()

    mock_dir = temp_dir(mkdtemp=True)
    os.environ["QQUTILS_TEST_DIR"] = mock_dir.as_posix()
    filename = f"test_{timestamp_millis()}.txt"
    p = under_home("qqutils_test", "subdir", filename, create=True, home_envvar="QQUTILS_TEST_DIR")
    assert mock_dir.as_posix() in p.as_posix()
    assert p.exists()

    os.environ["QQUTILS_TEST_DIR"] = "/nonexistent/dir"
    filename = f"test_{timestamp_millis()}.txt"
    try:
        p = under_home("qqutils_test", "subdir", filename, create=True, home_envvar="QQUTILS_TEST_DIR")
        assert False, "Expected ValueError due to nonexistent directory"
    except ValueError:
        assert True

    dirname = f"test_{timestamp_millis()}"
    p = under_home("qqutils_test", "subdir", dirname, all_dir=True)
    assert username in p.as_posix()
    assert not p.exists()
    assert not p.is_dir()

    dirname = f"test_{timestamp_millis()}"
    p = under_home("qqutils_test", "subdir", dirname, all_dir=True, create=True)
    assert username in p.as_posix()
    assert p.exists()
    assert p.is_dir()


def test_from_module():
    assert from_module().endswith(os.sep.join(("qqutils", "tests")))
    assert from_module(as_path=True).as_posix().endswith(os.sep.join(("qqutils", "tests")))
    assert from_module("test_osutils.py").endswith(os.sep.join(("qqutils", "tests", "test_osutils.py")))
    assert from_module("test_osutils.py", True).as_posix().endswith(os.sep.join(("qqutils", "tests", "test_osutils.py")))
