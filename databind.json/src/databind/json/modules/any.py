
import typing as t
from databind.core.mapper import Context, IConverter


class AnyConverter(IConverter):

  def convert(self, ctx: Context) -> t.Any:
    return ctx.value
