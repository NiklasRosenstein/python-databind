
import datetime
import typing as t
from databind.core.api import Context, Direction, IConverter, Value
from databind.core.objectmapper import SimpleModule


class DatetimeModule(SimpleModule):

  def __init__(self) -> None:
    super().__init__()
    conv = DatetimeJsonConverter()
    for type_ in (datetime.date, datetime.datetime, datetime.time):
      self.add_converter_for_type(type_, conv, Direction.Deserialize)
      self.add_converter_for_type(type_, conv, Direction.Serialize)


class DatetimeJsonConverter(IConverter):

  def convert(self, value: Value, ctx: Context) -> t.Any:
    print('--> date', ctx.direction, value)
    raise NotImplementedError
