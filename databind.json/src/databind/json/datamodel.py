
"""
Provides the #DatamodelModule that implements the de/serialization of JSON payloads for databind
schemas (see #databind.core.schema).
"""

import typing as t
from databind.core.api import Context, DeserializerEnvironment, IDeserializer, ISerializer, SerializerEnvironment
from databind.core.objectmapper import IModule
from databind.core.typehint import Datamodel, TypeHint


class DatamodelModule(IModule):

  # IModule
  def get_deserializer(self, type: TypeHint) -> IDeserializer:
    if isinstance(type, Datamodel):
      return DatamodelDeser()
    return None

  # IModule
  def get_serializer(self, type: TypeHint) -> ISerializer:
    if isinstance(type, Datamodel):
      return DatamodelDeser()
    return None


class DatamodelDeser(IDeserializer, ISerializer):

  def deserialize(self, ctx: Context[DeserializerEnvironment]) -> t.Any:
    print('--> deser', ctx)
    raise NotImplementedError  # TODO

  def serialize(self, ctx: Context[SerializerEnvironment]) -> t.Any:
    raise NotImplementedError  # TODO
