
import abc
import enum
import typing as t
from dataclasses import dataclass

from databind.core.annotations import Annotation, get_annotation
from databind.core.annotations.base import AnnotationsProvider
from databind.core.types.adapter import TypeHintAdapter
from databind.core.types.types import BaseType
from databind.core.types.schema import Field
from .location import Location, Position
from .settings import Settings

T = t.TypeVar('T', bound=Annotation)
T_Annotation = t.TypeVar('T_Annotation', bound=Annotation)


class Direction(enum.Enum):
  """
  Encodes the conversion direction in a #ConversionEnv.
  """

  #: Conversion takes place from some data format to a Python object.
  deserialize = enum.auto()

  #: Conversion takes place from a Python object to another data format.
  serialize = enum.auto()


class Converter(metaclass=abc.ABCMeta):
  """
  Interface for deserializers and serializers.
  """

  @abc.abstractmethod
  def convert(self, ctx: 'Context') -> t.Any: ...


class ConverterProvider(metaclass=abc.ABCMeta):
  """
  Provider for an #IConverter for a #TypeHint.
  """

  @abc.abstractmethod
  def get_converter(self, type_: BaseType, direction: 'Direction') -> Converter: ...

  Wrapper: t.Type['_ConverterProviderWrapper']


@dataclass
class Context:
  """
  Container for the information that is passed to an #IConverter for the de/serialization of a
  value (as denoted by the #direction). Converters may create a new #Context object referencing
  the original context in the #parent field to kick off the de/serialization of a sub value.
  """

  #: Reference to the parent #Value object.
  parent: t.Optional['Context']

  #: The type adapter used in this context.
  type_hint_adapter: TypeHintAdapter

  #: Provider for de-/serializers.
  converters: ConverterProvider

  #: Provider of annotations.
  annotations: AnnotationsProvider

  #: Settings for this conversion context (in addition to the mapper settings).
  settings: Settings

  #: The direction of the conversion.
  direction: Direction

  #: The value that is de/serialized in this context.
  value: t.Any

  #: The location of the value in the source data. This contains the type information for
  #: the #value, which is also accesible via #type.
  location: Location

  #: The #Field data from the schema that the value is de/serialized from/to. Can be used to
  #: read annotations that influence the conversion behaviour. Note that the #Field.type
  #: may be different from the #Location.type if the de/serialization is executed on a field
  #: representing a complex type (e.g., a list or map).
  field: Field

  def __str__(self) -> str:
    return f'Context(direction={self.direction.name}, value={_trunc(repr(self.value), 30)})'

  @property
  def type(self) -> BaseType:
    return self.location.type

  def push(self,
    type_: BaseType,
    value: t.Any,
    key: t.Union[str, int, None],
    field: t.Optional[Field] = None,
    filename: t.Optional[str] = None,
    position: t.Optional[Position] = None
  ) -> 'Context':
    location = self.location.push(type_, key, filename, position)
    return Context(self, self.type_hint_adapter, self.converters, self.annotations, self.settings, self.direction, value,
      location, field or Field(str(key or '$'), type_, []))

  def convert(self) -> t.Any:
    return self.converters.get_converter(self.location.type, self.direction).convert(self)

  def get_annotation(self, annotation_cls: t.Type[T_Annotation]) -> t.Optional[T_Annotation]:
    return self.field.get_annotation(annotation_cls) or \
      get_annotation(self.location.type.annotations, annotation_cls, None) or \
      self.annotations.get_global_annotation(annotation_cls)

  def error(self, message: str) -> 'ConversionError':
    return ConversionError(message, self.location)

  def type_error(self, *, expected: t.Union[str, t.Type, t.Tuple[t.Type, ...]]) -> 'ConversionError':
    if isinstance(expected, tuple):
      expected = '|'.join(x.__name__ for x in expected)
    elif isinstance(expected, type):
      expected = expected.__name__
    return self.error(
      f'expected `{expected}` to {self.direction.name.lower()} `{self.type}`, '
      f'got `{type(self.value).__name__}`')


@dataclass
class ConverterNotFound(Exception):
  type_: BaseType
  direction: Direction


@dataclass
class ConversionError(Exception):
  message: t.Union[str, Exception]
  location: Location

  def __str__(self) -> str:
    return f'{self.location}: {self.message}'


class _ConverterProviderWrapper(ConverterProvider):

  def __init__(self, func: t.Callable[[BaseType], Converter]) -> None:
    self._func = func

  def get_converter(self, type_: BaseType, direction: 'Direction') -> Converter:
    return self._func(type_, direction)  # type: ignore


ConverterProvider.Wrapper = _ConverterProviderWrapper


def _trunc(s: str, l: int) -> str:
  if len(s) > l:
    return s[:l] + '... '
  return s
