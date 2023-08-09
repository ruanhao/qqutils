from hprint import hprint
import click
from stopwatch import Stopwatch
from functools import partial, wraps
from icecream import Source
import inspect
import subprocess
import traceback
from .commutils import send_mail
from .osutils import (
    run_script,
    as_root,
    is_root,
    switch_dir,
    tmpdir,
    local_path,
    module_path,
)
from .netutils import (
    http_get, http_post, http_put, http_delete,
)
from datetime import datetime, timezone
import logging
import sys
from icecream import ic, install as install_ic
import tempfile
from logging.handlers import RotatingFileHandler
import os

_logger = logging.getLogger(__name__)

__all__ = [

    # PRINT UTILS
    'hprint',

    # SETUP UTILS
    'install_print_with_flush',

    # DATASCTRUCTURE MANIPULATION UTILS
    # 'chain_get',
    'pget',
    'flatten',
    'kvdict',
    'kdict',

    # EXCEPTION UTILS
    'sneaky',

    # NET UTILS
    'http_get',
    'http_post',
    'http_put',
    'http_delete',

    # MAIL
    'send_mail',

    # DATETIME UTILS
    'YmdHMS',
    'datetimestr',
    'pretty_duration',
    'utc_to_local',

    # LOGGING
    'pfatal',
    'pinfo',
    'pdebug',
    'configure_logging',

    # OS UTILS
    'bye',
    'goodbye',
    'run_script',
    'as_root',
    'is_root',
    'switch_dir',
    'tmpdir',
    'local_path',
    'module_path',


    # FUNCTION UTILS
    'cached',


    # DEBUG UTILS
    'assert_that',
    'simple_timing',
    'debug_timing',


    # MISC
    'write_to_clipboard',
    'prompt',
    'confirm',
    'pause',

]


def cached(func):
    obj = None

    @wraps(func)
    def inner(*args, **kwargs):
        nonlocal obj
        if obj is None:
            obj = func(*args, **kwargs)
        return obj
    return inner


def assert_that(condition_to_fulfill, msg):
    if not condition_to_fulfill:
        traceback.print_stack()
        bye(msg)


def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


def bye(msg, rc=1, logger=_logger):
    logger.error(f"see ya [{rc}]: {msg}")
    print(msg, file=sys.stderr)
    exit(rc)


def goodbye(msg=None, logger=_logger):
    if msg:
        logger.info(f"Bye bye: {msg}")
        print(msg)
    else:
        logger.info("goodbye")
    exit()


def pfatal(msg):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    logger = getattr(mod, 'logger', _logger)
    logger.critical(msg)
    bye(msg)


def pinfo(msg):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    logger = getattr(mod, 'logger', _logger)
    logger.info(msg)
    if logger.isEnabledFor(logging.INFO):
        print(msg)


def pdebug(msg):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    logger = getattr(mod, 'logger', _logger)
    logger.debug(msg)
    if logger.isEnabledFor(logging.DEBUG):
        print(msg)


def pretty_duration(seconds):
    TIME_DURATION_UNITS = (
        ('w', 60 * 60 * 24 * 7),
        ('d', 60 * 60 * 24),
        ('h', 60 * 60),
        ('m', 60),
        ('s', 1)
    )
    if seconds == 0:
        return 'inf'
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append('{}{}'.format(amount, unit))
    return ','.join(parts)


def datetimestr(ts0, fmt="%m/%d/%Y %H:%M:%S"):
    try:
        ts = int(ts0)
    except Exception:
        return ''
    if len(str(ts0)) > 10:
        ts = int(ts / 1000)
    date_time = datetime.fromtimestamp(ts)
    return date_time.strftime(fmt)


def YmdHMS():
    return datetime.now().strftime("%Y%m%d%H%M%S")


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


def pget(obj, key, default='n/a'):
    try:
        return chain_get(obj, key, default)
    except Exception:
        return default


def _ic_time_format():
    return f'\n{datetime.now()}| '


def configure_logging(name, level=None):
    level = level or logging.INFO
    # install_print_with_flush()
    ic.configureOutput(prefix=_ic_time_format, includeContext=True)
    ic.disable()
    install_ic()

    logging.basicConfig(
        handlers=[
            RotatingFileHandler(
                filename=os.path.join(tempfile.gettempdir(), name) + ".log",
                maxBytes=10 * 1024 * 1024,  # 10M
                backupCount=5),
            # logging.StreamHandler(),  # default to stderr
        ],
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p')
    if level == logging.DEBUG:
        import http.client as http_client
        http_client.HTTPConnection.debuglevel = 1
        http_client_logger = logging.getLogger("http.client")

        def __print_to_log(*args):
            # ic(args)
            http_client_logger.debug(" ".join(args))

        http_client.print = __print_to_log


# annotation
def debug_timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        # ts = time.time()
        stopwatch = Stopwatch(2)
        result = f(*args, **kw)
        # te = time.time()
        if _logger.isEnabledFor(logging.DEBUG):
            # click.echo(f'⏱ {stopwatch} |> [fn:]{f.__module__}.{f.__name__} | [args:] {args!r} | [kw:] {kw!r}', err=True)
            args = [repr(arg) for arg in args]
            kws = [f"{k}={repr(v)}" for k, v in kw.items()]
            all_args = ', '.join(args + kws)
            print(f'⏱ {stopwatch} |> {f.__module__}.{f.__name__}({all_args})', file=sys.stderr)
        return result
    return wrap


def simple_timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        stopwatch = Stopwatch(2)
        result = f(*args, **kw)
        print(f'Time: {stopwatch}', file=sys.stderr)
        return result
    return wrap


def write_to_clipboard(output):
    process = subprocess.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(output.encode())


def pause(msg='Press Enter to continue...', skip=False):
    if not skip:
        input(msg)


def confirm(abort=False):
    return click.confirm('Do you want to continue?', abort=abort)


def prompt(msg='Please enter:', type=str, default=None):
    value = click.prompt(msg, type=type, default=default)
    return value
