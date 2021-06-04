
import abc
import enum
import typing as t
from dataclasses import dataclass, field
from .annotations import Annotation
from .location import Location
from .typehint import TypeHint

T_Annotation = t.TypeVar('T_Annotation', bound=Annotation)


class Direction(enum.Enum):
  """
  Encodes the conversion direction in a #ConversionEnv.
  """

  #: Conversion takes place from some data format to a Python object.
  Deserialize = enum.auto()

  #: Conversion takes place from a Python object to another data format.
  Serialize = enum.auto()


class IConverter(metaclass=abc.ABCMeta):
  """
  Interface for deserializers and serializers.
  """

  @abc.abstractmethod
  def convert(self, value: 'Value', ctx: 'Context') -> t.Any: ...


class IConverterProvider(metaclass=abc.ABCMeta):
  """
  Provider for an #IConverter for a #TypeHint.
  """

  @abc.abstractmethod
  def get_converter(self, type: TypeHint, direction: 'Direction') -> IConverter: ...

  Wrapper: t.Type['_ConverterProviderWrapper']


class _ConverterProviderWrapper(IConverterProvider):

  def __init__(self, func: t.Callable[[TypeHint], IConverter]) -> None:
    self._func = func

  def get_converter(self, type: TypeHint, direction: 'Direction') -> IConverter:
    return self._func(type, direction)  # type: ignore


class IAnnotationsProvider(metaclass=abc.ABCMeta):
  """
  Interface to provide annotations for a given type or field in a type.
  """

  @abc.abstractmethod
  def get_type_annotation(self,
      type: t.Type,
      annotation_cls: t.Type[T_Annotation]
  ) -> t.Optional[T_Annotation]:
    ...

  @abc.abstractmethod
  def get_field_annotation(self,
      type: t.Type,
      field_name: str,
      annotation_cls: t.Type[T_Annotation]
  ) -> t.Optional[T_Annotation]:
    ...


class ITypeHintAdapter(metaclass=abc.ABCMeta):

  @abc.abstractmethod
  def adapt_type_hint(self, type: TypeHint) -> TypeHint: ...


@dataclass
class Context:
  """
  The context provides static information and implementations for the recursive conversion of
  a #Value.
  """

  annotations: IAnnotationsProvider = field(repr=False)
  converters: IConverterProvider = field(repr=False)
  direction: Direction

  def convert(self, value: 'Value') -> t.Any:
    converter = self.converters.get_converter(value.location.type, self.direction)
    return converter.convert(value, self)


@dataclass
class Value:
  """
  Container for a value that is passed to the #IConverter for conversion to or from Python.
  """

  current: t.Any
  location: Location
  parent: t.Optional['Value']


@dataclass
class ConverterNotFound(Exception):
  type: TypeHint
  direction: Direction


@dataclass
class ConversionError(Exception):
  message: t.Union[str, Exception]
  location: Location
