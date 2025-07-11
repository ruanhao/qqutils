# flake8: noqa
import sys

from hprint import hprint

from . import stringutils
from . import threadutils
from . import inspectutils
from . import commutils
from . import osutils
from . import logutils
from . import netutils
from . import funcutils
from . import dateutils
from . import datautils
from . import dbgutils
from . import dsutils
from . import urlutils
from . import cryptutils
from . import objutils
from . import asyncutils
from . import sqliteutils


CLICK_CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

__all__ = [
    'CLICK_CONTEXT_SETTINGS',
    'hprint',
]

for name, module in globals().copy().items():
    if name.startswith('__'):
        continue
    if isinstance(module, type(sys)) and name.endswith('utils') and hasattr(module, '__all__') and module.__all__:
        for item in module.__all__:
            if item not in __all__:
                globals()[item] = getattr(module, item)
                __all__.append(item)
