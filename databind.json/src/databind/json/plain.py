
import typing as t
from databind.core.api import Context, Direction, IConverter, Value
from databind.core.objectmapper import SimpleModule
from databind.core.typehint import TypeHint


class PlainJsonModule(SimpleModule):

  def __init__(self) -> None:
    super().__init__()
    conv = PlainJsonConverter()
    for type_ in (bool, float, int, str):
      self.add_converter_for_type(type_, conv, Direction.Deserialize)
      self.add_converter_for_type(type_, conv, Direction.Serialize)

  def get_converter(self, type: TypeHint, direction: Direction) -> IConverter:
    return super().get_converter(type, direction)


class PlainJsonConverter(IConverter):

  def convert(self, value: Value, ctx: Context) -> t.Any:
    print('--> plain', ctx.direction, value)
    raise NotImplementedError
