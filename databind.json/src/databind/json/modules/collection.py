
import typing as t
from databind.core.api import Context, ConverterNotFound, Direction, IConverter
from databind.core.objectmapper import Module
from databind.core.types import BaseType, CollectionType


class CollectionModule(Module):

  def get_converter(self, type_: BaseType, direction: Direction) -> IConverter:
    if isinstance(type_, CollectionType):
      return CollectionConverter()
    raise ConverterNotFound(type_, direction)


class CollectionConverter(IConverter):

  def __init__(self, json_type: t.Type[t.Collection] = list) -> None:
    self.json_type = json_type

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, CollectionType)

    if ctx.direction == Direction.serialize:
      if not isinstance(ctx.value, ctx.type.python_type):
        raise ctx.type_error(expected=ctx.type.python_type)
      python_type = self.json_type

    elif ctx.direction == Direction.deserialize:
      if not isinstance(ctx.value, t.Collection):
        raise ctx.type_error(expected=t.Collection)
      python_type = ctx.type.python_type

    else:
      assert False, ctx.direction

    return python_type(
      ctx.push(ctx.type.item_type, val, idx, ctx.field).convert()
      for idx, val in enumerate(ctx.value))
