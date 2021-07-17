
"""
Implements de/serialization of the #datetime types #datetime.date, #datetime.datetime and
#datetime.time to/from strings. The date/time format can be specified using the #datefmt()
annotation.

The date is parsed using the #nr.parsing.date module.
"""

import datetime
import typing as t
from databind.core import annotations as A
from databind.core.api import Context, ConversionError, Direction, IConverter, Context
from databind.core.objectmapper import SimpleModule
from databind.core.types import ConcreteType
from nr import preconditions
from nr.parsing.date import ISO_8601

T_DateTypes = t.TypeVar('T_DateTypes', bound=t.Union[datetime.date, datetime.time, datetime.datetime])


class DatetimeModule(SimpleModule):

  def __init__(self) -> None:
    super().__init__()
    conv = DatetimeJsonConverter()
    for type_ in (datetime.date, datetime.datetime, datetime.time):
      self.add_converter_for_type(type_, conv, Direction.deserialize)
      self.add_converter_for_type(type_, conv, Direction.serialize)


class DatetimeJsonConverter(IConverter):

  DEFAULT_DATE_FMT = A.datefmt(ISO_8601)
  DEFAULT_TIME_FMT = A.datefmt(ISO_8601)
  DEFAULT_DATETIME_FMT = A.datefmt(ISO_8601)

  def convert(self, ctx: Context) -> t.Any:
    preconditions.check_instance_of(ctx.type, ConcreteType)
    type_ = t.cast(ConcreteType, ctx.type).type
    datefmt = ctx.get_annotation(A.datefmt) or (
      self.DEFAULT_DATE_FMT if type_ == datetime.date else
      self.DEFAULT_TIME_FMT if type_ == datetime.time else
      self.DEFAULT_DATETIME_FMT if type_ == datetime.datetime else None)
    assert datefmt is not None

    if ctx.direction == Direction.deserialize:
      if not isinstance(ctx.value, str):
        raise ctx.type_error(expected='str')
      dt = datefmt.parse(type_, ctx.value)  # TODO(NiklasRosenstein): Rethrow as ConversionError
      assert isinstance(dt, type_)
      return dt

    else:
      if not isinstance(ctx.value, type_):
        raise ctx.type_error(expected=type_)
      return datefmt.format(ctx.value)
