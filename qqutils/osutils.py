import signal
import inspect
import os
import tempfile
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
import logging
import subprocess
import sys
import getpass
from contextlib import contextmanager
import click
from pathlib import Path


_logger = logging.getLogger(__name__)

# non blocking stream reader
nbsr_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='nbsr')


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

        nbsr_executor.submit(_populateQueue, self._s, self._q)

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


def tmpdir():
    return tempfile.gettempdir()


def from_cwd(*args):
    absolute = Path(os.path.join(os.getcwd(), *args))
    absolute.parent.mkdir(parents=True, exist_ok=True)
    return absolute


def _module_path(mod=None):
    if not mod:
        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])
    return os.path.dirname(mod.__file__)


def from_module(filename=None):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    if not filename:
        return _module_path(mod)
    return os.path.join(_module_path(mod), filename)


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
    return click.confirm('Do you want to continue?', abort=abort)


def prompt(msg='Please enter:', type=str, default=None, prompt_suffix=': '):
    value = click.prompt(msg, type=type, default=default, prompt_suffix=prompt_suffix)
    return value


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


def under_home(*path: str, all_dir=False, create=False) -> Path:
    """
    >>> under_home('a', 'b', 'c.txt')
    PosixPath('/Users/haoru/a/b/c.txt')
    >>>
    """
    p = Path.home().joinpath(*path).expanduser().resolve()
    if not create:
        return p
    if all_dir:
        p.mkdir(parents=True, exist_ok=True)
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch()
    return p
