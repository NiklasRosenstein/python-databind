
#![feature(dataclasses)]
#![feature(dict_ordered)]
#![feature(fstrings)]
#![feature(member_annotations)]

__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.8.1'

from ._converter import *
from ._datamodel import *
from ._locator import Locator
from ._union import *
from .utils import type_repr
