
import typing as t
from databind.core.annotations.base import AnnotationsRegistry
from databind.core.types.adapter import ChainTypeHintAdapter, DefaultTypeHintAdapter
from databind.core.types.schema import DataclassAdapter
from databind.core.types.types import ConcreteType

import deprecated
import nr.preconditions as preconditions

from databind.core.annotations import Annotation
from databind.core.types.types import BaseType
from databind.core.types.schema import DataclassAdapter, Field
from databind.core.types.union import UnionAdapter
from .converter import Context, ConverterNotFound, ConverterProvider, Direction, Context
from .module import SimpleModule
from .location import Location, Position
from .settings import Settings

__all__ = [
  'IModule',
  'SimpleModule',
  'ObjectMapper',
]

T = t.TypeVar('T')
T_Annotation = t.TypeVar('T_Annotation', bound=Annotation)


class ObjectMapper(AnnotationsRegistry, ChainTypeHintAdapter, SimpleModule):

  def __init__(self, *converters: ConverterProvider, name: str = None):
    AnnotationsRegistry.__init__(self)
    ChainTypeHintAdapter.__init__(self)
    SimpleModule.__init__(self, name)
    self.settings = Settings()
    for module in converters:
      self.add_converter_provider(module)

    self.add_type_hint_adapter(DefaultTypeHintAdapter())
    self.add_type_hint_adapter(UnionAdapter())
    self.add_type_hint_adapter(DataclassAdapter())
    self.add_type_hint_adapter_stop_condition(lambda t: isinstance(t, ConcreteType) and self._has_converter_for_conrete_type(t))

  def _has_converter_for_conrete_type(self, type_: ConcreteType) -> bool:
    # Type's for which we have a serializer or deserializer do not require adaptation.
    # The background here is that there can be #ConcreteType's that wrap a @dataclass
    # which would be adapter to an #ObjectType by the #DataclassAdapter unless we catch
    # that there is an explicit converter registered to handle that special case.
    try: self.get_converter(type_, Direction.deserialize)
    except ConverterNotFound: pass
    else: return True
    try: self.get_converter(type_, Direction.serialize)
    except ConverterNotFound: pass
    else: return True
    return False

  @classmethod
  @deprecated.deprecated("Use the ObjectMapper() constructor directly.")
  def default(cls, *converters: ConverterProvider, name: str = None) -> 'ObjectMapper':
    return cls(*converters, name=name)

  def convert(self,
    direction: Direction,
    value: t.Any,
    type_hint: t.Union[BaseType, t.Type[T]],
    filename: t.Optional[str] = None,
    position: t.Optional[Position] = None,
    key: t.Union[str, int, None] = None,
    annotations: t.Optional[t.List[t.Any]] = None,
    settings: t.Optional[t.List[t.Any]] = None,
  ) -> T:
    preconditions.check_instance_of(direction, Direction)
    type_ = self.adapt_type_hint(type_hint)
    field = Field('$', type_, annotations or [])
    loc = Location(None, type_, key, filename, position)
    ctx = Context(None, self, self, self,
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
  ) -> T:
    return self.convert(Direction.deserialize, value, type_hint, filename, pos, key, annotations, settings)

  def serialize(self,
    value: t.Any,
    type_hint: t.Union[BaseType, t.Type[T]],
    filename: str = None,
    pos: Position = None,
    key: t.Union[str, int] = None,
    annotations: t.List[t.Any] = None,
    settings: t.Optional[t.List[t.Any]] = None,
  ) -> t.Any:
    return self.convert(Direction.serialize, value, type_hint, filename, pos, key, annotations, settings)
