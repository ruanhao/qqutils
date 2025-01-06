from functools import wraps
import warnings
from typing import Any, Callable
import click
import logging
import time
import random

_logger = logging.getLogger(__name__)

# def run_click_command(command: click.Command, *args, **kwargs) -> typing.Any:
#     """Run a click command and return the result."""
#     _kwargs = {}
#     for param in command.params:
#         _kwargs[param.name] = param.default
#     _kwargs.update(kwargs)

#     while True:
#         try:
#             return command.callback(*args, **_kwargs)
#         except TypeError as te:
#             m = re.search(r"got an unexpected keyword argument '(.+)'", te.args[0])
#             if m:
#                 _kwargs.pop(m.group(1))
#             else:
#                 raise te


def run_click_command_with_obj(command: click.Command, obj: Any, *args, **kwargs) -> Any:
    """Run a click command and return the result."""
    ctx = click.Context(command, obj=obj)
    return ctx.invoke(command.callback, *args, **kwargs)


def run_click_command(command: click.Command, *args, **kwargs) -> Any:
    """Run a click command and return the result."""
    return run_click_command_with_obj(command, None, *args, **kwargs)


def cached(func):
    obj = None

    @wraps(func)
    def inner(*args, **kwargs):
        nonlocal obj
        if obj is None:
            obj = func(*args, **kwargs)
        return obj
    return inner


def deprecated(reason=None):

    def __wrapper(func):

        @wraps(func)
        def __inner(*args, **kwargs):
            warnings.simplefilter('always', UserWarning)  # turn off filter
            warnings.warn(
                f"DEPRECATED: {func.__name__}, {reason}" if reason else f"DEPRECATED: {func.__name__}",
                category=UserWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)

        return __inner

    return __wrapper


# define a retry decorator
def retry_with_exponential_backoff(
    func: Callable[..., Any],
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 3,
    errors: tuple = (TimeoutError,),
) -> Callable[..., Any]:
    """Retry a function with exponential backoff."""

    def wrapper(*args, **kwargs):
        # Initialize variables
        num_retries = 0
        delay = initial_delay

        # Loop until a successful response or max_retries is hit or an exception is raised
        while True:
            try:
                return func(*args, **kwargs)

            # Retry on specified errors
            except errors as e:
                # Increment retries
                num_retries += 1

                # Check if max retries has been reached
                if num_retries > max_retries:
                    _logger.error(f"Maximum number of retries ({max_retries}) exceeded.")
                    raise e

                # Increment the delay
                delay *= exponential_base * (1 + jitter * random.random())

                # Sleep for the delay
                time.sleep(delay)

            # Raise exceptions for any errors not specified
            except Exception as e:
                raise e

    return wrapper
