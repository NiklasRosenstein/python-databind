
import typing as t

import pytest
from databind.core.converter import Converter, ConversionError
from databind.core.mapper import NoMatchingConverter, ObjectMapper
from databind.core.module import Module
from databind.core.settings import Strict
from databind.json.converters import AnyConverter, PlainDatatypeConverter
from databind.json.direction import Direction


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
  assert mapper.convert('foobar', str) == 'foobar'
  assert mapper.convert(42, int) == 42

  with pytest.raises(ConversionError):
    assert mapper.convert('42', int)

  if direction == Direction.SERIALIZE:
    with pytest.raises(ConversionError):
      assert mapper.convert('42', int, settings=[Strict(False)])
  else:
    assert mapper.convert('42', int, settings=[Strict(False)]) == 42
