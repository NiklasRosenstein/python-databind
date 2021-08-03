
"""
Provides the #DecimalModule for decimal value de/serialization.
"""

import decimal
import typing as t
from databind.core import annotations as A, Context, ConcreteType, Direction, Converter
from nr import preconditions
from nr.optional import Optional


class DecimalJsonConverter(Converter):

  def convert(self, ctx: Context) -> t.Any:
    preconditions.check_instance_of(ctx.type, ConcreteType)
    preconditions.check_argument(t.cast(ConcreteType, ctx.type).type is decimal.Decimal, 'must be Decimal')
    context = Optional(ctx.get_annotation(A.precision))\
      .map(lambda b: b.to_context()).or_else(None)
    fieldinfo = ctx.get_annotation(A.fieldinfo) or A.fieldinfo()

    if ctx.direction == Direction.deserialize:
      if (not fieldinfo.strict and isinstance(ctx.value, (int, float))) or isinstance(ctx.value, str):
        return decimal.Decimal(ctx.value, context)
      raise ctx.type_error(expected='str')

    else:
      if not isinstance(ctx.value, decimal.Decimal):
        raise ctx.type_error(expected=decimal.Decimal)
      return str(ctx.value)
