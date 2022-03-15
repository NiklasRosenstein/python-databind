
import typing as t

import pytest
from databind.core.converter import Converter
from databind.core.mapper import NoMatchingConverter, ObjectMapper
from databind.core.module import Module
from databind.json.converters import AnyConverter, PlainDatatypeConverter


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
