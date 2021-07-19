
import typing as t
import pytest
from databind.core.api import ConversionError
from databind.core.objectmapper import ObjectMapper
from databind.core.types import from_typing
from databind.json import JsonModule

mapper = ObjectMapper.default(JsonModule())


def test_collection_mapper():
  assert mapper.deserialize(['abc', 'def'], t.Set[str]) == set(['abc', 'def'])
  assert sorted(mapper.serialize(set(['abc', 'def']), t.Set[str])) == ['abc', 'def']

  with pytest.raises(ConversionError) as excinfo:
    assert mapper.serialize(['abc', 'def'], t.Set[str]) == ['abc', 'def']
  assert 'expected `set` to serialize `SetType(ConcreteType(str))`, got `list`'
