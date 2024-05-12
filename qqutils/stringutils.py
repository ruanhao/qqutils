import click
import os
from itertools import cycle
from functools import partial


def style(text, fg, bold=False, underline=False):
    if os.getenv("QQUTILS_NO_STYLE") is not None:
        return text
    return click.style(text, fg=fg, bold=bold, underline=underline)


def green(text, bold=False, underline=False):
    return style(text, "green", bold=bold, underline=underline)


def red(text, bold=False, underline=False):
    return style(text, "red", bold=bold, underline=underline)


def yellow(text, bold=False, underline=False):
    return style(text, "yellow", bold=bold, underline=underline)


def blue(text, bold=False, underline=False):
    return style(text, "blue", bold=bold, underline=underline)


def cyan(text, bold=False, underline=False):
    return style(text, "cyan", bold=bold, underline=underline)


def magenta(text, bold=False, underline=False):
    return style(text, "magenta", bold=bold, underline=underline)


def bold(text):
    return style(text, None, bold=True)


def color_cycler(bold=False, underline=False, bright=False) -> cycle:
    colors = ['white', 'green', 'red', 'yellow', 'blue', 'cyan', 'magenta']
    if bright:
        colors = [f"bright_{c}" for c in colors]
    color_funcs = [partial(style, fg=c, bold=bold, underline=underline) for c in colors]
    return cycle(color_funcs)


def underline(text):
    return style(text, None, underline=True)
