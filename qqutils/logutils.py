import logging
from logging.handlers import RotatingFileHandler
from functools import partial, wraps
import tempfile
import os
from datetime import datetime
import inspect
import traceback
import sys
import click

_logger = logging.getLogger(__name__)


def setup_icecream(verbose=False):
    try:
        from icecream import ic, install

        def __ic_time_format():
            return f'{datetime.now()}|> '

        ic.configureOutput(prefix=__ic_time_format, includeContext=True)
        install()
        if not verbose:
            ic.disable()
    except ImportError:
        try:
            builtins = __import__('__builtin__')
        except ImportError:
            builtins = __import__('builtins')

        def __ic(*args):
            nonlocal verbose
            if verbose:
                print(f'{datetime.now()}|>', *args, flush=True, file=sys.stderr)

            if not args:  # E.g. ic().
                return None
            elif len(args) == 1:  # E.g. ic(1).
                return args[0]
            else:  # E.g. ic(1, 2, 3).
                return args
        setattr(builtins, 'ic', __ic)


def configure_logging(name, level=None, setup_ic=True):
    level = level or logging.INFO

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

    if setup_ic:
        setup_icecream(level == logging.DEBUG)


def _get_logger():
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    for k, v in mod.__dict__.items():
        if isinstance(v, logging.Logger):
            return v
    return _logger


def pfatal(msg):
    _get_logger().critical(msg)
    click.echo(msg, err=True)
    exit(1)


def pinfo(msg):
    logger = _get_logger()
    logger.info(msg)
    if logger.isEnabledFor(logging.INFO):
        click.echo(msg)


def perror(msg):
    logger = _get_logger()
    logger.error(msg)
    if logger.isEnabledFor(logging.ERROR):
        click.echo(msg, err=True)


def pwarning(msg):
    logger = _get_logger()
    logger.warning(msg)
    if logger.isEnabledFor(logging.WARNING):
        click.echo(msg, err=True)


def pdebug(msg, stderr=False):
    logger = _get_logger()
    logger.debug(msg)
    if logger.isEnabledFor(logging.DEBUG):
        click.echo(msg, err=stderr)


def pstderr(msg):
    click.echo(msg, err=True)


def install_print_with_flush():
    try:
        builtins = __import__('__builtin__')
    except ImportError:
        builtins = __import__('builtins')

    setattr(builtins, 'print0', print)
    setattr(builtins, 'print', partial(print, flush=True))


def _all_args_repr(args, kw):
    try:
        args_repr = [repr(arg) for arg in args]
        kws = [f"{k}={repr(v)}" for k, v in kw.items()]
        return ', '.join(args_repr + kws)
    except Exception:
        return "(?)"


def sneaky(logger: logging.Logger = None, console: bool = False):
    logger = logger or _get_logger()

    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kw):
            all_args = _all_args_repr(args, kw)
            try:
                return func(*args, **kw)
            except Exception as e:
                emsg = f"[{e}] sneaky call: {func.__name__}({all_args})"
                if logger:
                    logger.exception(emsg)
                if console:
                    print(emsg, traceback.format_exc(), file=sys.stderr, sep=os.linesep, flush=True)
        return wrapper
    return decorate


class LoggerAdapter(logging.LoggerAdapter):
    def __init__(self, logger, prefix=''):
        super(LoggerAdapter, self).__init__(logger, {})
        self.prefix = prefix

    def process(self, msg, kwargs):
        if self.prefix:
            return '[%s] %s' % (self.prefix, msg), kwargs
        else:
            return msg, kwargs
