
import typing as t
from databind.core.api import Context, ConversionError, Direction, IConverter, Value
from databind.core.objectmapper import SimpleModule
from databind.core.typehint import Concrete


class PlainDatatypeModule(SimpleModule):

  def __init__(self) -> None:
    super().__init__()
    conv = PlainJsonConverter()
    for type_ in (bool, float, int, str):
      self.add_converter_for_type(type_, conv, Direction.Deserialize)
      self.add_converter_for_type(type_, conv, Direction.Serialize)


class PlainJsonConverter(IConverter):

  def convert(self, value: Value, ctx: Context) -> t.Any:
    subject_type = t.cast(Concrete, value.location.type).type
    if subject_type in (int, float, str):
      # TODO(NiklasRosenstein): Configurable strict handling of incoming value
      return subject_type(value.current)
    raise NotImplementedError(subject_type, ctx.direction)
