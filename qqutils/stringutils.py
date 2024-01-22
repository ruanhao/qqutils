import click
import os


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


def underline(text):
    return style(text, None, underline=True)
