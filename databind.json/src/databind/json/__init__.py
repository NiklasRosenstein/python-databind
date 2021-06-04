
__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.12.0'

from databind.core.objectmapper import SimpleModule
from .datamodel import DatamodelModule
from .datetime import DatetimeModule
from .decimal import DecimalModule
from .plain import PlainDatatypeModule

__all__ = [
  'JsonModule',
]


class JsonModule(SimpleModule):
  """
  A composite of all modules for JSON de/serialization.
  """

  def __init__(self, name: str = None) -> None:
    super().__init__(name)
    self.add_module(DatamodelModule())
    self.add_module(DatetimeModule())
    self.add_module(DecimalModule())
    self.add_module(PlainDatatypeModule())
