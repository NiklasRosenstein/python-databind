
"""
Implements de/serialization of the #datetime types #datetime.date, #datetime.datetime and
#datetime.time to/from strings. The date/time format can be specified using the #A.datefmt()
annotation.

The date is parsed using the #nr.util.date module.
"""

import datetime
import typing as t
from databind.core import annotations as A
from databind.core import  Context, Converter, ConcreteType, Direction
from nr.util.date import ISO_8601, duration

T_DateTypes = t.TypeVar('T_DateTypes', bound=t.Union[datetime.date, datetime.time, datetime.datetime])


class DatetimeJsonConverter(Converter):

  DEFAULT_DATE_FMT = A.datefmt(ISO_8601)
  DEFAULT_TIME_FMT = A.datefmt(ISO_8601)
  DEFAULT_DATETIME_FMT = A.datefmt(ISO_8601)

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, ConcreteType), ctx.type
    type_ = t.cast(ConcreteType, ctx.type).type
    datefmt = ctx.get_annotation(A.datefmt) or (
      self.DEFAULT_DATE_FMT if type_ == datetime.date else
      self.DEFAULT_TIME_FMT if type_ == datetime.time else
      self.DEFAULT_DATETIME_FMT if type_ == datetime.datetime else None)
    assert datefmt is not None

    if ctx.direction == Direction.deserialize:
      if isinstance(ctx.value, type_):
        return ctx.value
      elif isinstance(ctx.value, str):
        dt = datefmt.parse(type_, ctx.value)  # TODO(NiklasRosenstein): Rethrow as ConversionError
        assert isinstance(dt, type_)
        return dt
      raise ctx.type_error(expected=f'str|{type_.__name__}')

    else:
      if not isinstance(ctx.value, type_):
        raise ctx.type_error(expected=type_)
      return datefmt.format(ctx.value)


class DurationConverter(Converter):

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, ConcreteType)

    if ctx.direction == Direction.serialize:
      if not isinstance(ctx.value, duration):
        raise ctx.type_error(expected=duration)
      return str(ctx.value)

    elif ctx.direction == Direction.deserialize:
      if not isinstance(ctx.value, str):
        raise ctx.type_error(expected=str)
      return duration.parse(ctx.value)   # TODO (@NiklasRosenstein): Reraise as ConversionError?
