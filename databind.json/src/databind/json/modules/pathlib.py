
import pathlib
import typing as t

from databind.core import ConcreteType, Context, Converter, Direction
from databind.core.mapper.converter import ConverterNotFound, ConverterProvider
from databind.core.types.types import BaseType


class PathlibConverter(Converter, ConverterProvider):

  def get_converter(self, type_: BaseType, direction: Direction) -> Converter:
    if isinstance(type_, ConcreteType) and issubclass(type_.type, pathlib.PurePath):
      return self
    raise ConverterNotFound(type_, direction)

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, ConcreteType)
    assert issubclass(ctx.type.type, pathlib.PurePath)

    if ctx.direction.is_serialize():
      if not isinstance(ctx.value, str):
        raise ctx.type_error(expected=str)
      return ctx.type.type(ctx.value)

    else:
      if not isinstance(ctx.value, ctx.type.type):
        raise ctx.type_error(expected=ctx.type.type)
      return str(ctx.value)
