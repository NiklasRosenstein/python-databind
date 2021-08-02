
import typing as t
from databind.core.annotations.base import AnnotationsRegistry

import deprecated
import nr.preconditions as preconditions

from databind.core.annotations import Annotation
from databind.core.types import BaseType, Field, from_typing, TypeHintConverter, root as root_type_converter
from .converter import Context, Direction, Context
from .module import Module, SimpleModule
from .location import Location, Position
from .settings import Settings

__all__ = [
  'IModule',
  'SimpleModule',
  'ObjectMapper',
]

T = t.TypeVar('T')
T_Annotation = t.TypeVar('T_Annotation', bound=Annotation)


class ObjectMapper(SimpleModule, AnnotationsRegistry):

  def __init__(self, *modules: Module, name: str = None):
    SimpleModule.__init__(self, name)
    AnnotationsRegistry.__init__(self)
    self.settings = Settings()
    for module in modules:
      self.add_module(module)

  @classmethod
  @deprecated.deprecated("Use the ObjectMapper() constructor directly.")
  def default(cls, *modules: Module, name: str = None) -> 'ObjectMapper':
    return cls(*modules, name=name)

  def convert(self,
    direction: Direction,
    value: t.Any,
    type_hint: t.Union[BaseType, t.Type[T]],
    filename: t.Optional[str] = None,
    position: t.Optional[Position] = None,
    key: t.Union[str, int, None] = None,
    annotations: t.Optional[t.List[t.Any]] = None,
    settings: t.Optional[t.List[t.Any]] = None,
    type_converter: t.Optional[TypeHintConverter] = None,
  ) -> T:
    preconditions.check_instance_of(direction, Direction)
    type_converter = type_converter or root_type_converter
    type_ = from_typing(type_hint, type_converter)
    field = Field('$', type_, annotations or [])
    loc = Location(None, type_, key, filename, position)
    ctx = Context(None, type_converter or root_type_converter, self, self,
      Settings(*(settings or []), parent=self.settings), direction, value, loc, field)
    return ctx.convert()

  def deserialize(self,
    value: t.Any,
    type_hint: t.Union[BaseType, t.Type[T]],
    filename: str = None,
    pos: Position = None,
    key: t.Union[str, int] = None,
    annotations: t.List[t.Any] = None,
    settings: t.Optional[t.List[t.Any]] = None,
    type_converter: t.Optional[TypeHintConverter] = None,
  ) -> T:
    return self.convert(Direction.deserialize, value, type_hint, filename, pos, key, annotations, settings, type_converter)

  def serialize(self,
    value: t.Any,
    type_hint: t.Union[BaseType, t.Type[T]],
    filename: str = None,
    pos: Position = None,
    key: t.Union[str, int] = None,
    annotations: t.List[t.Any] = None,
    settings: t.Optional[t.List[t.Any]] = None,
    type_converter: t.Optional[TypeHintConverter] = None,
  ) -> t.Any:
    return self.convert(Direction.serialize, value, type_hint, filename, pos, key, annotations, settings, type_converter)
