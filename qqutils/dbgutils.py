from stopwatch import Stopwatch
import traceback
import logging
import sys
from functools import wraps

_logger = logging.getLogger(__name__)


def assert_that(condition_to_fulfill, msg):
    if not condition_to_fulfill:
        traceback.print_stack()
        print(msg, file=sys.stderr)
        exit(1)


def simple_timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        stopwatch = Stopwatch(2)
        result = f(*args, **kw)
        print(f'Time: {stopwatch}', file=sys.stderr)
        return result
    return wrap


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
