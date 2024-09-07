from functools import wraps
import typing
import click


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


def run_click_command_with_obj(command: click.Command, obj: typing.Any, *args, **kwargs) -> typing.Any:
    """Run a click command and return the result."""
    ctx = click.Context(command, obj=obj)
    return ctx.invoke(command.callback, *args, **kwargs)


def run_click_command(command: click.Command, *args, **kwargs) -> typing.Any:
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
