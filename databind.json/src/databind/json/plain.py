
import typing as t
from databind.core.api import Context, ConversionError, Direction, IConverter, Context
from databind.core.objectmapper import SimpleModule
from databind.core.typehint import Concrete


class PlainDatatypeModule(SimpleModule):

  def __init__(self) -> None:
    super().__init__()
    conv = PlainJsonConverter()
    for type_ in (bool, float, int, str):
      self.add_converter_for_type(type_, conv, Direction.deserialize)
      self.add_converter_for_type(type_, conv, Direction.serialize)


class PlainJsonConverter(IConverter):

  def convert(self, ctx: Context) -> t.Any:
    subject_type = t.cast(Concrete, ctx.location.type).type
    if subject_type in (int, float, str):
      # TODO(NiklasRosenstein): Configurable strict handling of incoming value
      return subject_type(ctx.value)
    raise NotImplementedError(subject_type, ctx.direction)
