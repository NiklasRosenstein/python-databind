
import enum
import typing as t
from databind.core import BaseType, ConcreteType, Context, ConverterNotFound, Converter, ConverterProvider,  Direction


class EnumConverter(Converter, ConverterProvider):
  """
  Converter for enum values.

  * #enum.IntEnum subclasses are serialized to integers.
  * #enum.Enum subclasses are serialized to strings (from the enum value name).
  """

  def get_converter(self, type_: BaseType, direction: Direction) -> Converter:
    if isinstance(type_, ConcreteType) and issubclass(type_.type, enum.Enum):
      return self
    raise ConverterNotFound(type_, direction)

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, ConcreteType)
    assert issubclass(ctx.type.type, enum.Enum)

    if ctx.direction == Direction.serialize:
      if not isinstance(ctx.value, ctx.type.type):
        raise ctx.type_error(expected=ctx.type.type)
      if issubclass(ctx.type.type, enum.IntEnum):
        return ctx.value.value
      if issubclass(ctx.type.type, enum.Enum):
        return ctx.value.name

    elif ctx.direction == Direction.deserialize:
      if issubclass(ctx.type.type, enum.IntEnum):
        if not isinstance(ctx.value, int):
          raise ctx.type_error(expected=int)
        return ctx.type.type(ctx.value)
      if issubclass(ctx.type.type, enum.Enum):
        if not isinstance(ctx.value, str):
          raise ctx.type_error(expected=str)
        try:
          return ctx.type.type[ctx.value]
        except KeyError:
          raise ctx.error(f'{ctx.value!r} is not a member of enumeration {ctx.type}')

    assert False
