import os
import getpass
from qqutils.osutils import (
    from_module,
    from_cwd,
    from_path_str,
    temp_dir,
    under_home,
    load_dotenv,
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


def test_load_dotenv_case_empty():
    assert not load_dotenv(filename=".env_not_exists")


def test_load_dotenv():
    os.environ["TEST_VAR"] = "original_value"
    timestamp_str = str(timestamp_millis())
    with open(from_cwd(".env"), "w") as f:
        f.write(f"TEST_VAR={timestamp_str}\nTIMESTAMP={timestamp_str}\nTEST_VAR2=${{TIMESTAMP}}\n")
    assert load_dotenv()
    assert os.getenv("TEST_VAR") == timestamp_str
    assert os.getenv("TEST_VAR2") == timestamp_str


def test_load_dotenv_case_not_overide():
    os.environ["TEST_VAR"] = "original_value"
    timestamp_str = str(timestamp_millis())
    with open(from_cwd(".env"), "w") as f:
        f.write(f"TEST_VAR={timestamp_str}\n")
    assert load_dotenv(override=False)
    assert os.getenv("TEST_VAR") == "original_value"


def test_load_dotenv_case_interpolate_false():
    timestamp_str = str(timestamp_millis())
    with open(from_cwd(".env"), "w") as f:
        f.write(f"TIMESTAMP={timestamp_str}\nTEST_VAR={{TIMESTAMP}}\n")
    assert load_dotenv(interpolate=False)
    assert os.getenv("TEST_VAR") == "{TIMESTAMP}"
