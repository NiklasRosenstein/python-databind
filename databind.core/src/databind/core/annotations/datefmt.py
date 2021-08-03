
"""
Provides the #datefmt() annotation that can be used to control the date format(s) that are used
during de/serialization of #datetime.date, #datetime.datetime and #datetime.time objects.
"""

import datetime
import typing as t
from dataclasses import dataclass

from nr.parsing.date import date_format, time_format, datetime_format, format_set

from databind.core.annotations.base import Annotation

Dtype = t.Union[datetime.date, datetime.time, datetime.datetime]
Formatter = t.Union[date_format, time_format, datetime_format]
T_Input = t.Union[str, date_format, time_format, datetime_format, format_set]
T_Dtype = t.TypeVar('T_Dtype', bound=Dtype)
T_Formatter = t.TypeVar('T_Formatter', bound=Formatter)


def _formulate_parse_error(formats: t.Sequence[t.Any], s: t.Any) -> ValueError:
  return ValueError(f'"{s}" does not match date formats ({len(formats)}):' +
    ''.join(f'\n  | {x.format_str}' for x in formats))


@dataclass
class datefmt(Annotation):
  """
  An annotation to describe the date format(s) used for parsing and formatting
  dates when de-/serialized from/to a string.
  """

  formats: t.Sequence[T_Input]

  def __init__(self, *formats: T_Input) -> None:
    if not formats:
      raise ValueError('need at least one date format')
    self.formats = formats

  def __iter_formats(self, type_: t.Type[T_Formatter]) -> t.Iterable[T_Formatter]:
    for fmt in self.formats:
      if isinstance(fmt, str):
        yield type_.compile(fmt)  # type: ignore
      elif type(fmt) == type_:
        yield fmt
      elif isinstance(fmt, format_set):
        yield from getattr(fmt, type_.__name__ + 's')
      #else:
      #  raise RuntimeError(f'bad date format type: {type(fmt).__name__}')

  def parse(self, type_: t.Type[T_Dtype], value: str) -> T_Dtype:
    format_t: t.Type[Formatter]
    format_t, method_name = {  # type: ignore
      datetime.date: (date_format, 'parse_date'),
      datetime.time: (time_format, 'parse_time'),
      datetime.datetime: (datetime_format, 'parse_datetime'),
    }[type_]
    for fmt in self.__iter_formats(format_t):  # type: ignore
      try:
        return getattr(fmt, method_name)(value)
      except ValueError:
        pass
    raise _formulate_parse_error(list(self.__iter_formats(format_t)), value)  # type: ignore

  def format(self, dt: T_Dtype) -> str:
    format_t: t.Type[Formatter]
    format_t, method_name = {  # type: ignore
      datetime.date: (date_format, 'format_date'),
      datetime.time: (time_format, 'format_time'),
      datetime.datetime: (datetime_format, 'format_datetime'),
    }[type(dt)]
    for fmt in self.__iter_formats(format_t):  # type: ignore
      try:
        return getattr(fmt, method_name)(dt)
      except ValueError:
        pass
    raise _formulate_parse_error(list(self.__iter_formats(format_t)), dt)  # type: ignore
