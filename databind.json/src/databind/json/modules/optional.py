
import typing as t
from databind.core.mapper import Context, Converter
from databind.core.types import OptionalType


class OptionalConverter(Converter):

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, OptionalType)
    if ctx.value is None:
      return None
    return ctx.push(ctx.type.type, ctx.value, None, ctx.field).convert()
