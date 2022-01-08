
import enum
import typing as t

from databind.core import BaseType, ConcreteType, Context, ConverterNotFound, Converter, ConverterProvider,  Direction
from databind.core import annotations as A


class EnumConverter(Converter, ConverterProvider):
  """
  Converter for enum values.

  * #enum.IntEnum subclasses are serialized to integers.
  * #enum.Enum subclasses are serialized to strings (from the enum value name).
  """

  def get_converters(self, type_: BaseType, direction: Direction) -> t.Iterable[Converter]:
    if isinstance(type_, ConcreteType) and issubclass(type_.type, enum.Enum):
      yield self

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, ConcreteType)
    assert issubclass(ctx.type.type, enum.Enum)

    if ctx.direction == Direction.serialize:
      if not isinstance(ctx.value, ctx.type.type):
        raise ctx.type_error(expected=ctx.type.type)
      if issubclass(ctx.type.type, enum.IntEnum):
        return ctx.value.value
      if issubclass(ctx.type.type, enum.Enum):
        name = ctx.value.name
        alias = ctx.annotations.get_field_annotation(ctx.type.type, name, A.alias)
        if alias and alias.aliases:
          return alias.aliases[0]
        return name

    elif ctx.direction == Direction.deserialize:
      if issubclass(ctx.type.type, enum.IntEnum):
        if not isinstance(ctx.value, int):
          raise ctx.type_error(expected=int)
        return ctx.type.type(ctx.value)
      if issubclass(ctx.type.type, enum.Enum):
        if not isinstance(ctx.value, str):
          raise ctx.type_error(expected=str)
        for enum_value in ctx.type.type:
          alias = ctx.annotations.get_field_annotation(ctx.type.type, enum_value.name, A.alias)
          if alias and ctx.value in alias.aliases:
            return enum_value
        try:
          return ctx.type.type[ctx.value]
        except KeyError:
          raise ctx.error(f'{ctx.value!r} is not a member of enumeration {ctx.type}')

    assert False
