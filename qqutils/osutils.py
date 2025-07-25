import signal
import os
import tempfile
from queue import Queue, Empty
import logging
import subprocess
import sys
import getpass
from contextlib import contextmanager
from pathlib import Path
from .funcutils import deprecated, cached


__all__ = (
    'bye',
    'goodbye',
    'run_script',
    'as_root',
    'is_root',
    'switch_dir',
    'tmpdir',                   # deprecated
    'temp_dir',
    'temp_file',
    'from_cwd',
    'from_module',
    'write_to_clipboard',
    'prompt',
    'confirm',
    'pause',
    'add_suffix',
    'modify_extension',
    'from_path_str',
    'under_home',
    'backup',                   # backup a file
    'normalize_path',
    'random_string',
    'os_open_file',
    'load_dotenv',
)

_logger = logging.getLogger(__name__)


def _find_dotenv(
    filename: str = ".env",
    raise_error_if_not_found: bool = False,
    usecwd: bool = False,
) -> str:
    """
    Search in increasingly higher folders for the given file

    Returns path to the file if found, or an empty string otherwise
    """
    from dotenv.main import _walk_to_root

    def _is_interactive():
        """Decide whether this is running in a REPL or IPython notebook"""
        if hasattr(sys, "ps1") or hasattr(sys, "ps2"):
            return True
        try:
            main = __import__("__main__", None, None, fromlist=["__file__"])
        except ModuleNotFoundError:
            return False
        return not hasattr(main, "__file__")

    def _is_debugger():
        return sys.gettrace() is not None

    if usecwd or _is_interactive() or _is_debugger() or getattr(sys, "frozen", False):
        # Should work without __file__, e.g. in REPL or IPython notebook.
        path = os.getcwd()
    else:
        # will work for .py files
        frame = sys._getframe()
        current_file = __file__

        while frame.f_code.co_filename == current_file or not os.path.exists(
            frame.f_code.co_filename
        ):
            assert frame.f_back is not None
            frame = frame.f_back
        frame_filename = frame.f_code.co_filename
        path = os.path.dirname(os.path.abspath(frame_filename))

    for dirname in _walk_to_root(path):
        check_path = os.path.join(dirname, filename)
        if os.path.isfile(check_path):
            return check_path

    if raise_error_if_not_found:
        raise IOError("File not found")

    return ""

def load_dotenv(
        *,
        filename: str = '.env',
        from_cwd: bool = False,
        interpolate: bool = True,
        override: bool = True,
        verbose: bool = False,
) -> bool:
    """
    Load environment variables from a .env file in the current directory or the user's home directory.
    """
    import dotenv
    dotenv_path = _find_dotenv(filename=filename, usecwd=from_cwd)
    if dotenv_path:
        r = dotenv.load_dotenv(dotenv_path=dotenv_path, interpolate=interpolate, override=override, verbose=verbose)
        _logger.debug(f"Loading environment variables from {dotenv_path}: {r}")
        return r
    else:
        _logger.warning(f"No {filename} file found, skipping loading environment variables.")
        return False


# non blocking stream reader
@cached
def _get_nbsr_executor():
    from concurrent.futures import ThreadPoolExecutor
    return ThreadPoolExecutor(max_workers=4, thread_name_prefix='nbsr')


class UnexpectedEndOfStream(Exception):
    pass


class NonBlockingStreamReader:

    def __init__(self, stream, logger=None):
        '''
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        '''

        self._s = stream
        self._q = Queue()
        self.logger = logger or _logger

        def _populateQueue(stream, queue):
            '''
            Collect lines from 'stream' and put them in 'quque'.
            '''

            self.logger.info("Starting readline ...")
            while True:
                line = stream.readline()
                if line:
                    queue.put(line)
                else:
                    self.logger.info("Stream EOF")
                    return

        _get_nbsr_executor().submit(_populateQueue, self._s, self._q)

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None, timeout=timeout)
        except Empty:
            self.logger.debug(f"NBSR timeout ({timeout}s)")
            return None

    def close(self):
        self._s.close()


class NoKeyboardInterrupt:

    def __enter__(self):
        self.signal_received = False
        self.old_handler = signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig, frame):
        # self.signal_received = (sig, frame)
        logging.debug('SIGINT received. Ignoring KeyboardInterrupt.')

    def __exit__(self, type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        # if self.signal_received:
        #     self.old_handler(*self.signal_received)


def run_script(command, capture=False, realtime=False, opts='', dry=False, logger=_logger):
    """When realtime == True, stderr will be redirected to stdout"""
    logger.debug(f"Running subprocess: [{command}] (capture: {capture})")
    if dry:
        print(command)
        return
    preexec_options = {}
    if sys.platform.startswith('win'):
        # https://msdn.microsoft.com/en-us/library/windows/desktop/ms684863(v=vs.85).aspx
        # CREATE_NEW_PROCESS_GROUP=0x00000200 -> If this flag is specified, CTRL+C signals will be disabled
        preexec_options['creationflags'] = 0x00000200
    else:
        preexec_options['preexec_fn'] = lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
    process = subprocess.Popen(
        ['/bin/bash', f'-c{opts}', command],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT if realtime else subprocess.PIPE if capture else subprocess.DEVNULL,
        encoding='utf-8',
        bufsize=1,              # line buffered
        **preexec_options,
    )
    nbsr = None
    try:
        if not realtime:
            stdout, stderr = process.communicate()
            rc = process.returncode
        else:
            stdout, stderr = '', ''
            last_n_lines = []
            nbsr = NonBlockingStreamReader(process.stdout)
            while True:
                realtime_output = nbsr.readline(15)  # block 15s at most
                if process.poll() is not None:
                    break
                if realtime_output:
                    logger.debug(f"[{process.pid}:stdout] " + realtime_output.rstrip())
                    print(realtime_output.rstrip(), flush=True)
                    last_n_lines.append(realtime_output.rstrip())
                    last_n_lines = last_n_lines[-10:]
                    if capture:
                        stdout += realtime_output
            rc = process.poll()
            stdout, stderr = stdout.rstrip(), None if realtime else process.stderr.read().rstrip()
        if rc:
            logger.critical(f"Subprocess Failed ({rc}): {os.linesep.join(last_n_lines).rstrip() if realtime else stderr}")
        if rc and not capture:
            raise Exception(f"Subprocess Failed ({rc}): {os.linesep.join(last_n_lines).rstrip() if realtime else stderr}")
        return rc, stdout, stderr
    except KeyboardInterrupt:
        logger.info("Sending SIGINT to subprocess ..")
        process.send_signal(signal.SIGINT)
        logger.info("Waiting subprocess to exit gracefully..")
        with NoKeyboardInterrupt():
            process.wait()
    finally:
        if nbsr:
            nbsr.close()


# annotation
def as_root(func):
    def inner_function(*args, **kwargs):
        if not is_root():
            _logger.error('Must run as root.')
            print('Please run as root.', file=sys.stderr)
            exit(1)
        func(*args, **kwargs)
    return inner_function


def is_root():
    return getpass.getuser() == 'root'


@contextmanager
def switch_dir(dir=None):
    if dir is None:
        dir = tempfile.mkdtemp()
    orig_cwd = os.getcwd()
    Path(dir).mkdir(parents=True, exist_ok=True)
    _logger.info(f"Switching CWD to [{dir}]")
    os.chdir(dir)
    try:
        yield
    finally:
        _logger.info(f"Switching CWD BACK to [{orig_cwd}]")
        os.chdir(orig_cwd)


@deprecated(reason="Use temp_dir instead")
def tmpdir():
    return tempfile.gettempdir()


@deprecated(reason="Use temp_file instead")
def tmpfile(filename, create_tempdir=False) -> Path:
    tmp_dir_path = tmpdir(create_tempdir)
    tmp_dir_path.mkdir(parents=True, exist_ok=True)
    return tmp_dir_path / filename


@deprecated(reason="Use temp_file instead")
def create_temp_file(filename: str) -> str:
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, filename)
    with open(file_path, 'w'):
        pass
    return file_path


def temp_dir(mkdtemp=False) -> Path:
    d = tempfile.mkdtemp() if mkdtemp else tempfile.gettempdir()
    dpath = Path(d)
    dpath.mkdir(parents=True, exist_ok=True)
    return dpath


def temp_file(filename, mkdtemp=False, touch=True) -> Path:
    p = temp_dir(mkdtemp) / filename
    if touch:
        p.touch()
    return p


def from_cwd(*args) -> str:
    absolute = Path(os.path.join(os.getcwd(), *args))
    absolute.parent.mkdir(parents=True, exist_ok=True)
    return absolute


def _module_path(mod=None):
    import inspect
    if not mod:
        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])
    return os.path.dirname(mod.__file__)


def from_module(filename: str = None, as_path: bool = False) -> str | Path:
    import inspect
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    path: str = None
    if not filename:
        path = _module_path(mod)
    else:
        path = os.path.join(_module_path(mod), filename)
    return Path(path) if as_path else path


def bye(msg, rc=1, logger=_logger):
    logger.critical(f"Exit with return code: {rc}: {msg}")
    print(msg, file=sys.stderr)
    exit(rc)


def goodbye(msg=None, logger=_logger):
    if msg:
        logger.info(f"Exit normally: {msg}")
        print(msg)
    else:
        logger.info("Exit normally")
    exit()


def write_to_clipboard(output):
    process = subprocess.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(output.encode())


def pause(msg='Press Enter to continue...', skip=False):
    if not skip:
        input(msg)


def confirm(abort=False):
    import click
    return click.confirm('Do you want to continue?', abort=abort)


def prompt(msg='Please enter', type=str, default=None, prompt_suffix=': ', hide=False):
    if hide:
        import pwinput
        while True:
            if default is not None:
                _prompt = f"{msg} [{default}]{prompt_suffix}"
            else:
                _prompt = msg + prompt_suffix
            ret0 = pwinput.pwinput(prompt=_prompt)
            if default is not None and not ret0:
                ret = default
            else:
                ret = ret0
            try:
                return type(ret)
            except ValueError:
                print(f"Error: '{ret}' is not a valid {type}.")
    import click
    return click.prompt(
        msg,
        type=type,
        default=default,
        show_default=True,
        prompt_suffix=prompt_suffix,
    )


def add_suffix(filename: str, suffix: str) -> str:
    filename, file_extension = os.path.splitext(filename)
    return f"{filename}{suffix}{file_extension}"


def modify_extension(filename: str, extension: str) -> str:
    filename, _file_extension = os.path.splitext(filename)
    if extension.startswith('.'):
        return f"{filename}{extension}"
    return f"{filename}.{extension}"


def from_path_str(path_str: str, default=None, logger=_logger) -> Path:
    """
    >>> from_path_str('~/a/b/c.txt')
    PosixPath('/Users/haoru/a/b/c.txt')
    >>>
    """
    if not path_str:
        return default
    path = Path(path_str).expanduser().resolve()
    if not path.exists():
        logger.error(f"Path does not exist: {path_str}")
        return default
    return path


def under_home(*path: str, all_dir: bool = False, create: bool = False, home_envvar: str = None) -> Path:
    """
    >>> under_home('a', 'b', 'c.txt')
    PosixPath('/Users/haoru/a/b/c.txt')
    >>>
    """
    root = Path.home()
    if home_envvar:
        root = Path(os.environ.get(home_envvar, Path.home()))
        if not root.exists() or not root.is_dir():
            raise ValueError(f"Environment variable {home_envvar} does not point to a valid directory: {root}")
        if not os.access(root, os.W_OK):
            raise PermissionError(f"Cannot write to directory: {root}")

    p = root.joinpath(*path).expanduser().resolve()
    if not create:
        return p
    if all_dir:
        p.mkdir(parents=True, exist_ok=True)
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch()
    return p


# >>> normalize_path('~/a/b/../c/../d/e')
# '/home/paul/a/d/e'
def normalize_path(path) -> str:
    p = Path(os.path.normpath(path))
    if p.as_posix().startswith('~'):
        return p.expanduser().as_posix()
    else:
        return p.as_posix()


def random_string(length=8):
    return os.urandom(length // 2).hex()


def os_open_file(filepath: str):
    import platform
    if platform.system() == 'Darwin':       # macOS
        subprocess.call(('open', filepath))
    elif platform.system() == 'Windows':    # Windows
        os.startfile(filepath)
    else:                                   # linux variants
        subprocess.call(('xdg-open', filepath))


def backup(path: Path, suffix: str = '.bak', force: bool = False):
    if not path.exists():
        return
    bak_path = path.with_suffix(suffix)
    if bak_path.exists() and not force:
        return
    with path.open('rb') as source:
        with bak_path.open('wb') as target:
            target.write(source.read())
