
"""
Provides the #DecimalModule for decimal value de/serialization.
"""

import decimal
import typing as t
from databind.core import annotations as A, Context, ConcreteType, Direction, Converter
from nr.util.optional import Optional


class DecimalJsonConverter(Converter):

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, ConcreteType), ctx.type
    assert ctx.type.type is decimal.Decimal, f'must be Decial, got {ctx.type.type}'

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
