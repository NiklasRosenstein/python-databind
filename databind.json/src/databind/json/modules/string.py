
import dataclasses
import typing as t

from databind.core import BaseType, ConcreteType, Context, Converter, ConverterNotFound, ConverterProvider, Direction


@dataclasses.dataclass
class StringConverter(Converter, ConverterProvider):
  """
  This helper class makes it easy to define a converter for string based types in serialized form.
  """

  from_string: t.Callable[[t.Type, str], t.Any]
  to_string: t.Optional[t.Callable[[t.Type, t.Any], str]] = None
  matches: t.Optional[t.Callable[[t.Type], bool]] = None

  def get_converters(self, type_: BaseType, direction: Direction) -> t.Iterable[Converter]:
    if self.matches is None:
      raise RuntimeError('StringConverter cannot be as a ConverterProvider unless StringConverter.matches is set')
    if isinstance(type_, ConcreteType) and self.matches(type_.type):
      yield self

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, ConcreteType)

    if ctx.direction.is_deserialize():
      if not isinstance(ctx.value, str):
        raise ctx.type_error(expected=str)
      try:
        return self.from_string(ctx.type.type, ctx.value)
      except (TypeError, ValueError) as exc:
        raise ctx.error(str(exc))

    else:
      if not isinstance(ctx.value, ctx.type.type):
        raise ctx.type_error(expected=ctx.type.type)
      if self.to_string is None:
        return str(ctx.value)
      else:
        return self.to_string(ctx.type.type, ctx.value)
