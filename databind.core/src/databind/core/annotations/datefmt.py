
"""
Provides the #datefmt() annotation that can be used to control the date format(s) that are used
during de/serialization of #datetime.date, #datetime.datetime and #datetime.time objects.
"""

import datetime
import typing as t
from dataclasses import dataclass

from nr.parsing.date import date_format, time_format, datetime_format, format_set
from nr.stream import Stream

from . import Annotation

_format_t = t.Union[
  str,
  date_format,
  time_format,
  datetime_format,
  format_set]
_internal_t = t.TypeVar('_internal_t', bound=t.Union[date_format, time_format, datetime_format])
_date_t = t.TypeVar('_date_t', bound=t.Union[datetime.date, datetime.time, datetime.datetime])


def _formulate_parse_error(formats: t.Sequence[t.Any], s: str) -> ValueError:
  return ValueError(f'"{s}" does not match date formats ({len(formats)}):' +
    ''.join(f'\n  | {x.format_str}' for x in formats))


@dataclass
class datefmt(Annotation):
  """
  An annotation to describe the date format(s) used for parsing and formatting
  dates when de-/serialized from/to a string.
  """

  formats: t.List[_format_t]

  def __init__(self, *formats: _format_t) -> None:
    if not formats:
      raise ValueError('need at least one date format')
    self.formats = formats

  def __iter_formats(self, type_: t.Type[_internal_t]) -> t.Iterable[_internal_t]:
    for fmt in self.formats:
      if isinstance(str):
        yield type_.compile(fmt)
      elif type(fmt) == type_:
        yield fmt
      elif isinstance(fmt, format_set):
        yield from getattr(fmt, type_.__name__ + 's')
      else:
        raise RuntimeError(f'bad date format type: {type(fmt).__name__}')

  def parse(self, type_: t.Type[_date_t], value: str) -> _date_t:
    format_t, method_name = {
      datetime.date: (date_format, 'parse_date'),
      datetime.time: (time_format, 'parse_time'),
      datetime.datetime: (datetime_format, 'parse_datetime'),
    }
    for fmt in self.__iter_formats(format_t):
      try:
        return getattr(fmt, method_name)(value)
      except ValueError:
        pass
    raise _formulate_parse_error(list(self.__iter_formats(format_t)))

  def format(self, dt: _date_t) -> str:
    format_t, method_name = {
      datetime.date: (date_format, 'format_date'),
      datetime.time: (time_format, 'format_time'),
      datetime.datetime: (datetime_format, 'format_datetime'),
    }
    for fmt in self.__iter_formats(format_t):
      try:
        return getattr(fmt, method_name)(dt)
      except ValueError:
        pass
    raise _formulate_parse_error(list(self.__iter_formats(format_t)))
