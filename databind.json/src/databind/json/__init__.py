
__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.12.0'

from databind.core.objectmapper import IModule, SimpleModule
from .dataclass import DataclassModule
from .datamodel import DatamodelModule

__all__ = [
  'DataclassModule',
  'DatamodelModule',
  'JsonModule',
]


class JsonModule(SimpleModule):
  """
  A composite of all modules for JSON de/serialization.
  """

  def __init__(self, name: str = None) -> None:
    super().__init__(name)
    self.add_module(DataclassModule())
    self.add_module(DatamodelModule())
