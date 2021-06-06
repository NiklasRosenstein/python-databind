
import decimal
import typing as t
from databind.core import annotations as A
from databind.core.api import Context, Direction, IConverter, Context
from databind.core.objectmapper import SimpleModule
from databind.core.typehint import Concrete
from nr import preconditions
from nr.optional import Optional


class DecimalModule(SimpleModule):

  def __init__(self) -> None:
    super().__init__()
    conv = DecimalJsonConverter()
    self.add_converter_for_type(decimal.Decimal, conv, Direction.deserialize)
    self.add_converter_for_type(decimal.Decimal, conv, Direction.serialize)


class DecimalJsonConverter(IConverter):

  def convert(self, ctx: Context) -> t.Any:
    preconditions.check_instance_of(ctx.type, Concrete)
    preconditions.check_argument(t.cast(Concrete, ctx.type).type is decimal.Decimal, 'must be Decimal')
    context = Optional(ctx.get_annotation(A.precision))\
      .map(lambda b: b.to_context()).or_else(None)

    if ctx.direction == Direction.deserialize:
      if not isinstance(ctx.value, str):
        raise ctx.type_error(expected='str')
      # TODO(NiklasRosenstein): Allow int/float as source type if enabled per annotation.
      return decimal.Decimal(ctx.value, context)

    else:
      if not isinstance(ctx.value, decimal.Decimal):
        raise ctx.type_error(expected=decimal.Decimal)
      return str(ctx.value)
