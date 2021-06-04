
"""
Provides the #datefmt() annotation that can be used to control the date format(s) that are used
during de/serialization of #datetime.date, #datetime.datetime and #datetime.time objects.
"""

import datetime
import typing as t
from dataclasses import dataclass
from . import Annotation
from nr.parsing import date as _nrdate
from nr.stream import Stream

_DateFmtSource = t.Union[str, _nrdate.DatetimeFormat, _nrdate.DatetimeFormatSet]


@dataclass
class datefmt(Annotation):
  primary_format: _DateFmtSource
  accepted_formats: t.List[_DateFmtSource]

  def __init__(self, primary_format: _DateFmtSource, *accepted_formats: _DateFmtSource) -> None:
    self.primary_format = primary_format
    self.accepted_formats = list(accepted_formats)
    self.__cached_format: t.Optional[_nrdate.DatetimeFormat] = None

  @property
  def __format(self) -> _nrdate.DatetimeFormat:
    if self.__cached_format is not None:
      return self.__cached_format
    formats: t.List[_nrdate.DatetimeFormat] = []
    for fmt in Stream([[self.primary_format], self.accepted_formats]).concat():
      if isinstance(fmt, str):
        formats.append(_nrdate.root_option_set.create_date_format(fmt))
      elif isinstance(fmt, _nrdate.DatetimeFormatSet):
        formats.extend(fmt)
      elif isinstance(fmt, _nrdate.DatetimeFormat):
        formats.append(fmt)
      else:
        raise TypeError(f'expected str/DatetimeFormat/DatetimeFormatSet, got {type(fmt).__name__}')
    self.__cached_format = _nrdate.DatetimeFormatSet('@datefmt()', formats)
    return self.__cached_format

  def parse(self, value: str) -> datetime.datetime:
    return self.__format.parse(value)

  def format(self, dt: datetime.datetime) -> str:
    return self.__format.format(dt)
