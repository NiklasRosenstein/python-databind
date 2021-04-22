
import abc
import typing as t
from dataclasses import dataclass

from databind.core.objectmapper.typehint import TypeHint
from .location import Location
from ..annotations import Annotation

T_Annotation = t.TypeVar('T_Annotation', bound=Annotation)


class IDeserializer(metaclass=abc.ABCMeta):
  """
  Interface for deserializers.
  """

  def deserialize(self, ctx: 'DeserializerContext') -> t.Any: ...


class ISerializer(metaclass=abc.ABCMeta):
  """
  Interface for serializers.
  """

  def serialize(self, ctx: 'SerializerContext') -> t.Any: ...


class IDeserializerProvider(metaclass=abc.ABCMeta):
  """
  Provider for deserializers.
  """

  def get_deserializer(self, type: TypeHint) -> IDeserializer: ...


class ISerializerProvider(metaclass=abc.ABCMeta):
  """
  Provider for serializers.
  """

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


_T_Context = t.TypeVar('_T_Context', bound='_BaseContext')


@dataclass
class _BaseContext(t.Generic[_T_Context]):
  parent: t.Optional[_T_Context]
  value: t.Any
  location: Location
  annotations: IAnnotationsProvider


@dataclass
class DeserializerContext(_BaseContext['DeserializerContext']):
  deserializers: IDeserializerProvider

  def error(self, message: t.Union[str, Exception]) -> 'DeserializationError':
    return DeserializationError(message, self.location)


@dataclass
class SerializerContext(_BaseContext['SerializerContext']):
  serializers: ISerializerProvider

  def error(self, message: t.Union[str, Exception]) -> 'SerializationError':
    return SerializationError(message, self.location)


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
