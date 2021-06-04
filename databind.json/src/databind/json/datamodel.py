
"""
Provides the #DatamodelModule that implements the de/serialization of JSON payloads for databind
schemas (see #databind.core.schema).
"""

import typing as t
from databind.core.api import Context, ConverterNotFound, Direction, IConverter, Value
from databind.core.objectmapper import Module
from databind.core.typehint import Datamodel, TypeHint


class DatamodelModule(Module):

  def get_converter(self, type: TypeHint, direction: Direction) -> IConverter:
    if isinstance(type, Datamodel):
      return DatamodelDeserializer() if direction == Direction.Deserialize else DatamodelSerializer()
    raise ConverterNotFound(type, direction)


class DatamodelDeserializer(IConverter):

  def convert(self, value: Value, ctx: Context) -> t.Any:
    print('--> deser', ctx)
    raise NotImplementedError  # TODO


class DatamodelSerializer(IConverter):

  def convert(self, value: Value, ctx: Context) -> t.Any:
    print('--> ser', ctx)
    raise NotImplementedError  # TODO
