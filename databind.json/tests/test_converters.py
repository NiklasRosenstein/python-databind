
import datetime
import decimal
import enum
import typing as t
import typing_extensions as te
from xmlrpc.client import SERVER_ERROR

import pytest
from databind.core.converter import Converter, ConversionError
from databind.core.mapper import ObjectMapper
from databind.core.module import Module
from databind.core.settings import Alias, Strict
from databind.json.converters import AnyConverter, DatetimeConverter, DecimalConverter, DurationConverter, \
  EnumConverter, OptionalConverter, PlainDatatypeConverter
from databind.json.direction import Direction
from nr.util.date import duration


def make_mapper(converters: t.List[Converter]) -> ObjectMapper:
  module = Module('testing')
  for converter in converters:
    module.register(converter)
  mapper = ObjectMapper()
  mapper.add_module(module)
  return mapper


def test_any_converter():
  mapper = make_mapper([AnyConverter()])
  assert mapper.convert('foobar', t.Any) == 'foobar'
  assert mapper.convert(42, t.Any) == 42
  assert mapper.convert(t.Any, t.Any) == t.Any


@pytest.mark.parametrize('direction', (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_plain_datatype_converter(direction: Direction):
  mapper = make_mapper([PlainDatatypeConverter(direction)])

  # test strict

  assert mapper.convert('foobar', str) == 'foobar'
  assert mapper.convert(42, int) == 42
  with pytest.raises(ConversionError):
    assert mapper.convert('42', int)

  # test non-strict

  mapper.settings.add_global(Strict(False))
  if direction == Direction.SERIALIZE:
    with pytest.raises(ConversionError):
      assert mapper.convert('42', int)

  else:
    assert mapper.convert('42', int) == 42
    with pytest.raises(ConversionError):
      mapper.convert('foobar', int)


@pytest.mark.parametrize('direction', (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_decimal_converter(direction: Direction):
  mapper = make_mapper([DecimalConverter(direction)])

  pi = decimal.Decimal('3.141592653589793')
  if direction == Direction.SERIALIZE:
    assert mapper.convert(pi, decimal.Decimal) == str(pi)

  else:
    assert mapper.convert(str(pi), decimal.Decimal) == pi
    with pytest.raises(ConversionError):
      assert mapper.convert(3.14, decimal.Decimal)
    assert mapper.convert(3.14, decimal.Decimal, settings=[Strict(False)]) == decimal.Decimal(3.14)


@pytest.mark.parametrize('direction', (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_enum_converter(direction: Direction):
  mapper = make_mapper([EnumConverter(direction)])

  class Pet(enum.Enum):
    CAT = enum.auto()
    DOG = enum.auto()
    LION: te.Annotated[int, Alias('KITTY')] = enum.auto()

  if direction == Direction.SERIALIZE:
    assert mapper.convert(Pet.CAT, Pet) == 'CAT'
    assert mapper.convert(Pet.DOG, Pet) == 'DOG'
    assert mapper.convert(Pet.LION, Pet) == 'KITTY'
  else:
    assert mapper.convert('CAT', Pet) == Pet.CAT
    assert mapper.convert('DOG', Pet) == Pet.DOG
    assert mapper.convert('KITTY', Pet) == Pet.LION

  class Flags(enum.IntEnum):
    A = 1
    B = 2

  if direction == Direction.SERIALIZE:
    assert mapper.convert(Flags.A, Flags) == 1
    assert mapper.convert(Flags.B, Flags) == 2
    with pytest.raises(ConversionError):
      assert mapper.convert(Flags.A | Flags.B, Flags)
  else:
    assert mapper.convert(1, Flags) == Flags.A
    assert mapper.convert(2, Flags) == Flags.B
    with pytest.raises(ConversionError):
      assert mapper.convert(3, Flags)


def test_optional_converter():
  mapper = make_mapper([OptionalConverter(), PlainDatatypeConverter(Direction.SERIALIZE)])
  assert mapper.convert(42, t.Optional[int]) == 42
  assert mapper.convert(None, t.Optional[int]) == None
  assert mapper.convert(42, int) == 42
  with pytest.raises(ConversionError):
    assert mapper.convert(None, int)


@pytest.mark.parametrize('direction', (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_datetime_converter(direction: Direction):
  mapper = make_mapper([DatetimeConverter(direction)])

  tests = [
    (datetime.time(11, 30, 10), '11:30:10.0'),
    (datetime.date(2022, 2, 4), '2022-02-04'),
    (datetime.datetime(2022, 2, 4, 11, 30, 10), '2022-02-04T11:30:10.0'),
  ]

  for py_value, str_value in tests:
    if direction == Direction.SERIALIZE:
      assert mapper.convert(py_value, type(py_value)) == str_value
    else:
      assert mapper.convert(str_value, type(py_value)) == py_value


@pytest.mark.parametrize('direction', (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_duration_converter(direction: Direction):
  mapper = make_mapper([DurationConverter(direction)])

  tests = [
    (duration(2, 1, 4, 0, 3), 'P2Y1M4WT3H'),
  ]

  for py_value, str_value in tests:
    if direction == Direction.SERIALIZE:
      assert mapper.convert(py_value, duration) == str_value
    else:
      assert mapper.convert(str_value, duration) == py_value
