
__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.12.0'

from databind.core.objectmapper import SimpleModule
from .modules.collection import CollectionModule
from .modules.datetime import DatetimeModule
from .modules.decimal import DecimalModule
from .modules.object import ObjectModule
from .modules.plain import PlainDatatypeModule
from .modules.union import UnionModule

__all__ = [
  'JsonModule',
]


class JsonModule(SimpleModule):
  """
  A composite of all modules for JSON de/serialization.
  """

  def __init__(self, name: str = None) -> None:
    super().__init__(name)
    self.add_module(DatetimeModule())
    self.add_module(DecimalModule())
    self.add_module(PlainDatatypeModule())
    self.add_module(CollectionModule())
    self.add_module(ObjectModule())
    self.add_module(UnionModule())
