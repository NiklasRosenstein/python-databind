
"""
Provides the #ObjectTypeModule that implements the de/serialization of JSON payloads for databind
schemas (see #databind.core.schema).
"""

import typing as t
from databind.core import annotations as A
from databind.core.api import Context, ConverterNotFound, Direction, IConverter, Context
from databind.core.objectmapper import Module
from databind.core.types import ObjectType, BaseType
from .unionclass import UnionclassConverter


class ObjectTypeModule(Module):

  def get_converter(self, type: BaseType, direction: Direction) -> IConverter:
    if isinstance(type, ObjectType):
      if type.schema.unionclass is not None:
        return UnionclassConverter()
      return ObjectTypeConverter()
    raise ConverterNotFound(type, direction)


class ObjectTypeConverter(IConverter):

  def convert(self, ctx: Context) -> t.Any:
    print('--> datamodel', ctx)
    raise NotImplementedError  # TODO
