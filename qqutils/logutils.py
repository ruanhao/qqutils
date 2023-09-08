import logging
from logging.handlers import RotatingFileHandler
from functools import partial, wraps
import tempfile
import os
from datetime import datetime
import inspect
import traceback
import sys

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
                print(f'{datetime.now()}|>', *args)

            if not args:  # E.g. ic().
                return None
            elif len(args) == 1:  # E.g. ic(1).
                return args[0]
            else:  # E.g. ic(1, 2, 3).
                return args
        setattr(builtins, 'ic', __ic)


def configure_logging(name, level=None, setup_ic=False):
    level = level or logging.INFO
    # install_print_with_flush()

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


def perror(msg):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    logger = getattr(mod, 'logger', _logger)
    logger.error(msg)
    if logger.isEnabledFor(logging.ERROR):
        print(msg, file=sys.stderr)


def pwarning(msg):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    logger = getattr(mod, 'logger', _logger)
    logger.warning(msg)
    if logger.isEnabledFor(logging.WARNING):
        print(msg, file=sys.stderr)


def pdebug(msg):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    logger = getattr(mod, 'logger', _logger)
    logger.debug(msg)
    if logger.isEnabledFor(logging.DEBUG):
        print(msg)


def install_print_with_flush():
    try:
        builtins = __import__('__builtin__')
    except ImportError:
        builtins = __import__('builtins')

    setattr(builtins, 'print0', print)
    setattr(builtins, 'print', partial(print, flush=True))


def sneaky(logger=None, console=False):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kw):
            try:
                return func(*args, **kw)
            except Exception as e:
                tb = traceback.format_exc()
                if logger:
                    logger.error("%s: \n%s", e, str(tb))
                if console:
                    print(f"{tb}")
        return wrapper
    return decorate
