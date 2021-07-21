
from datetime import date, time, datetime
from nr.parsing.date import date_format, time_format, datetime_format
from nr.parsing.date.format_sets import ISO_8601
from .datefmt import datefmt


def test_datefmt_formatters():
  assert datefmt(date_format.compile('%Y-%d-%m')).parse(date, '2021-01-02') == date(2021, 2, 1)
  assert datefmt(time_format.compile('%H:%M')).parse(time, '12:24') == time(12, 24)
  assert datefmt(datetime_format.compile('%Y-%d-%mT%H:%M')).parse(datetime, '2021-01-02T12:24') == datetime(2021, 2, 1, 12, 24)

  assert datefmt(date_format.compile('%Y-%d-%m')).format(date(2021, 2, 1)) == '2021-01-02'
  assert datefmt(time_format.compile('%H:%M')).format(time(12, 24)) == '12:24'
  assert datefmt(datetime_format.compile('%Y-%d-%mT%H:%M')).format(datetime(2021, 2, 1, 12, 24)) == '2021-01-02T12:24'


def test_datefmt_raw():
  assert datefmt('%Y-%d-%m').parse(date, '2021-01-02') == date(2021, 2, 1)
  assert datefmt('%H:%M').parse(time, '12:24') == time(12, 24)
  assert datefmt('%Y-%d-%mT%H:%M').parse(datetime, '2021-01-02T12:24') == datetime(2021, 2, 1, 12, 24)

  assert datefmt('%Y-%d-%m').format(date(2021, 2, 1)) == '2021-01-02'
  assert datefmt('%H:%M').format(time(12, 24)) == '12:24'
  assert datefmt('%Y-%d-%mT%H:%M').format(datetime(2021, 2, 1, 12, 24)) == '2021-01-02T12:24'


def test_datefmt_format_set():
  assert datefmt(ISO_8601).parse(date, '2021-01-02') == date(2021, 1, 2)
  assert datefmt(ISO_8601).parse(time, '12:24') == time(12, 24)
  assert datefmt(ISO_8601).parse(datetime, '2021-01-02T12:24') == datetime(2021, 1, 2, 12, 24)

  assert datefmt(ISO_8601).format(date(2021, 2, 1)) == '2021-02-01'
  assert datefmt(ISO_8601).format(time(12, 24)) == '12:24:00.0'
  assert datefmt(ISO_8601).format(datetime(2021, 2, 1, 12, 24)) == '2021-02-01T12:24:00.0'
