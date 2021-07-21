
import typing_extensions as te
from datetime import date, datetime, time, timezone
from databind.core.annotations.datefmt import datefmt
from databind.core.objectmapper import ObjectMapper
from databind.json import JsonModule
from nr.parsing.date.duration import duration

mapper = ObjectMapper.default(JsonModule())


def test_datetime():
  assert mapper.deserialize('2021-03-28', date) == date(2021, 3, 28)
  assert mapper.deserialize('21:01:54Z', time) == time(21, 1, 54)  # TODO(NiklasRosenstein): Missing timezone, fix in nr.parsing.date
  assert mapper.deserialize('2021-03-28T21:01:54Z', datetime) == datetime(2021, 3, 28, 21, 1, 54, 0, timezone.utc)
  assert mapper.serialize(date(2021, 3, 28), date) == '2021-03-28'
  assert mapper.serialize(time(21, 1, 54, tzinfo=timezone.utc), time) == '21:01:54.0Z'
  assert mapper.serialize(datetime(2021, 3, 28, 21, 1, 54, 0, timezone.utc), datetime) == '2021-03-28T21:01:54.0Z'
  assert mapper.serialize(datetime(2021, 3, 28, 21, 1, 54, 0, timezone.utc), te.Annotated[datetime, datefmt('%Y-%m-%d')]) == '2021-03-28'


def test_duration():
  assert mapper.deserialize('P20DT1H', duration) == duration(days=20, hours=1)
  assert mapper.serialize(duration(days=20, hours=1), duration) == 'P20DT1H'
