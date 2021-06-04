
import decimal
import typing as t
from databind.core import annotations as A
from databind.core.api import Context, Direction, IConverter, Value
from databind.core.objectmapper import SimpleModule
from databind.core.typehint import Concrete
from nr import preconditions
from nr.optional import Optional


class DecimalModule(SimpleModule):

  def __init__(self) -> None:
    super().__init__()
    conv = DecimalJsonConverter()
    self.add_converter_for_type(decimal.Decimal, conv, Direction.Deserialize)
    self.add_converter_for_type(decimal.Decimal, conv, Direction.Serialize)


class DecimalJsonConverter(IConverter):

  def convert(self, value: Value, ctx: Context) -> t.Any:
    preconditions.check_instance_of(value.type, Concrete)
    preconditions.check_argument(t.cast(Concrete, value.type).type is decimal.Decimal, 'must be Decimal')
    context = Optional(ctx.get_annotation(value, A.precision))\
      .map(lambda b: b.to_context()).or_else(None)

    if ctx.direction == Direction.Deserialize:
      if not isinstance(value.current, str):
        raise ctx.type_error(value, expected='str')
      # TODO(NiklasRosenstein): Allow int/float as source type if enabled per annotation.
      return decimal.Decimal(value.current, context)

    else:
      if not isinstance(value.current, decimal.Decimal):
        raise ctx.type_error(value, expected=decimal.Decimal)
      return str(value.current)
