
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

  def __init__(self) -> None:
    super().__init__()
    self.add_module(DataclassModule())
    self.add_module(DatamodelModule())
