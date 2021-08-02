
import typing as t
from databind.core.mapper import Context, Converter


class AnyConverter(Converter):

  def convert(self, ctx: Context) -> t.Any:
    return ctx.value
