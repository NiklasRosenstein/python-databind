
import decimal
import typing as t
from databind.core.api import Context, Direction, IConverter, Value
from databind.core.objectmapper import SimpleModule


class DecimalModule(SimpleModule):

  def __init__(self) -> None:
    super().__init__()
    conv = DecimalJsonConverter()
    self.add_converter_for_type(decimal.Decimal, conv, Direction.Deserialize)
    self.add_converter_for_type(decimal.Decimal, conv, Direction.Serialize)


class DecimalJsonConverter(IConverter):

  def convert(self, value: Value, ctx: Context) -> t.Any:
    print('--> decimal', ctx.direction, value)
    raise NotImplementedError
