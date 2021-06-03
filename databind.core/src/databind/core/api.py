
import abc
import typing as t
from dataclasses import dataclass
from .annotations import Annotation
from .location import Location
from .typehint import TypeHint

T_Annotation = t.TypeVar('T_Annotation', bound=Annotation)
_T_Environment = t.TypeVar('_T_Environment', bound='_Environment')


class IDeserializer(metaclass=abc.ABCMeta):
  """
  Interface for deserializers.
  """

  @abc.abstractmethod
  def deserialize(self, ctx: 'Context[DeserializerEnvironment]') -> t.Any: ...


class ISerializer(metaclass=abc.ABCMeta):
  """
  Interface for serializers.
  """

  @abc.abstractmethod
  def serialize(self, ctx: 'Context[SerializerEnvironment]') -> t.Any: ...


class IDeserializerProvider(metaclass=abc.ABCMeta):
  """
  Provider for deserializers.
  """

  @abc.abstractmethod
  def get_deserializer(self, type: TypeHint) -> IDeserializer: ...


class ISerializerProvider(metaclass=abc.ABCMeta):
  """
  Provider for serializers.
  """

  @abc.abstractmethod
  def get_serializer(self, type: TypeHint) -> ISerializer: ...


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
class _Environment():
  annotations: IAnnotationsProvider


@dataclass
class DeserializerEnvironment(_Environment):
  deserializers: IDeserializerProvider

  def error(self, message: t.Union[str, Exception]) -> 'DeserializationError':
    return DeserializationError(message, self.location)


@dataclass
class SerializerEnvironment(_Environment):
  serializers: ISerializerProvider

  def error(self, message: t.Union[str, Exception]) -> 'SerializationError':
    return SerializationError(message, self.location)


@dataclass
class Context(t.Generic[_T_Environment]):
  parent: t.Optional['Context[_T_Environment]']
  env: _T_Environment
  value: t.Any
  location: Location


@dataclass
class DeserializerNotFound(Exception):
  type: TypeHint


@dataclass
class SerializerNotFound(Exception):
  type: TypeHint


@dataclass
class DeserializationError(Exception):
  message: t.Union[str, Exception]
  location: Location


@dataclass
class SerializationError(Exception):
  message: t.Union[str, Exception]
  location: Location
