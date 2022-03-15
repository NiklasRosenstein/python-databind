
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
  assert mapper.convert_value('foobar', t.Any) == 'foobar'
  assert mapper.convert_value(42, t.Any) == 42
  assert mapper.convert_value(t.Any, t.Any) == t.Any


def test_plain_datatype_converter_serialize():
  mapper = make_mapper([PlainDatatypeConverter(Direction.SERIALIZE)])
  assert mapper.convert_value('foobar', str) == 'foobar'
  assert mapper.convert_value(42, int) == 42

  with pytest.raises(ConversionError):
    assert mapper.convert_value('42', int)

  mapper.settings.add_global(Strict(False))
  assert mapper.convert_value('42', int)
