import click
import os
from itertools import cycle
from functools import partial
from rich.console import Console
from rich.markdown import Markdown
from typing import Dict


def print_markdown(text: str, **kwargs: Dict) -> None:
    console = Console()
    md = Markdown(text)
    console.print(md, **kwargs)


def style(text, fg, bold=False, underline=False):
    if os.getenv("QQUTILS_NO_STYLE") is not None:
        return text
    return click.style(text, fg=fg, bold=bold, underline=underline)


def white(text, bold=False, underline=False):
    return style(text, "white", bold=bold, underline=underline)


def green(text, bold=False, underline=False):
    return style(text, "green", bold=bold, underline=underline)


def bright_black(text, bold=False, underline=False):
    return style(text, "bright_black", bold=bold, underline=underline)


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


def format_bytes(size: int, scale: int = 1) -> (float, str):
    size = int(size)
    power = 2**10
    n = 0
    power_labels = {0: 'B', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        size = round(size, scale)
        n += 1
    return size, power_labels[n]
