
"""
Implements de/serialization of the #datetime types #datetime.date, #datetime.datetime and
#datetime.time to/from strings. The date/time format can be specified using the #datefmt()
annotation.

The date is parsed using the #nr.parsing.date module.
"""

import datetime
import typing as t
from databind.core import annotations as A
from databind.core.api import Context, ConversionError, Direction, IConverter, Value
from databind.core.objectmapper import SimpleModule
from databind.core.typehint import Concrete
from nr import preconditions
from nr.parsing.date import Iso8601, parse_date

T_DateTypes = t.TypeVar('T_DateTypes', bound=t.Union[datetime.date, datetime.time, datetime.datetime])


def trim_datetime(dt: datetime.datetime, type_: t.Type[T_DateTypes]) -> T_DateTypes:
  if type_ == datetime.datetime:
    return t.cast(T_DateTypes, dt)
  elif type_ == datetime.date:
    return t.cast(T_DateTypes, dt.date())
  elif type_ == datetime.time:
    return t.cast(T_DateTypes, dt.time())
  else:
    assert False, (dt, type_)


def expand_to_datetime(v: T_DateTypes) -> datetime.datetime:
  if isinstance(v, datetime.datetime):
    return v
  elif isinstance(v, datetime.date):
    return datetime.datetime(v.year, v.month, v.day)
  elif isinstance(v, datetime.time):
    return datetime.datetime(1970, 1, 1, v.hour, v.min, v.second)
  else:
    assert False, v


class DatetimeModule(SimpleModule):

  def __init__(self) -> None:
    super().__init__()
    conv = DatetimeJsonConverter()
    for type_ in (datetime.date, datetime.datetime, datetime.time):
      self.add_converter_for_type(type_, conv, Direction.Deserialize)
      self.add_converter_for_type(type_, conv, Direction.Serialize)


class DatetimeJsonConverter(IConverter):

  DEFAULT_DATEFMT = A.datefmt(Iso8601())

  def convert(self, value: Value, ctx: Context) -> t.Any:
    preconditions.check_instance_of(value.type, Concrete)
    type_ = t.cast(Concrete, value.type).type
    datefmt = value.get_annotation(ctx, A.datefmt) or self.DEFAULT_DATEFMT

    if ctx.direction == Direction.Deserialize:
      if not isinstance(value.current, str):
        raise value.type_error(expected='str')
      dt = datefmt.parse(value.current)  # TODO(NiklasRosenstein): Rethrow as ConversionError
      return trim_datetime(dt, type_)

    else:
      if not isinstance(value.current, type_):
        raise value.type_error(expected=type_.__name__)
      return datefmt.format(expand_to_datetime(value.current))
