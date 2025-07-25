from contextlib import contextmanager
import traceback
import logging
import sys
from functools import wraps
from attr import define
import time
from typing import Callable

__all__ = (
    'assert_that',
    'simple_timing',
    'debug_timing',
    'time_measurer',
)

_logger = logging.getLogger(__name__)


@define
class Timer:
    msg: str
    start: float = 0.0
    end: float = 0.0

    def __enter__(self):
        self.start = time.perf_counter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.perf_counter()
        print(f"[Timer:{self.msg}] {self.end - self.start:.02f}s")


def assert_that(condition_to_fulfill, msg):
    if not condition_to_fulfill:
        traceback.print_stack()
        print(msg, file=sys.stderr)
        exit(1)


def simple_timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        from stopwatch import Stopwatch
        stopwatch = Stopwatch(2)
        try:
            return f(*args, **kw)
        finally:
            print(f'Time: {stopwatch}', file=sys.stderr)
    return wrap


# annotation
def debug_timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        from stopwatch import Stopwatch
        # ts = time.time()
        stopwatch = Stopwatch(2)
        result = f(*args, **kw)
        # te = time.time()
        if _logger.isEnabledFor(logging.DEBUG):
            # click.echo(f'⏱ {stopwatch} |> [fn:]{f.__module__}.{f.__name__} | [args:] {args!r} | [kw:] {kw!r}', err=True)
            args = [repr(arg) for arg in args]
            kws = [f"{k}={repr(v)}" for k, v in kw.items()]
            all_args = ', '.join(args + kws)
            print(f'⏱ {stopwatch} |> {f.__module__}.{f.__name__}({all_args})', file=sys.stderr, flush=True)
        return result
    return wrap


@contextmanager
def time_measurer(msg: str = None, digits: int = 2) -> Callable[[], float]:
    import click
    from stopwatch import Stopwatch
    stopwatch = Stopwatch(digits)
    duration = stopwatch.duration
    if msg is not None:
        click.echo(msg if msg else 'Running...', err=True, nl=False)
    yield lambda: round(duration, digits)
    duration = stopwatch.duration
    if msg is not None:
        click.echo(f"({duration:.{digits}f}s)", err=True)
