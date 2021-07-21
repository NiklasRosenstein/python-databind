
import typing as t
from databind.core.objectmapper import ObjectMapper
from databind.core.types import from_typing
from databind.json import JsonModule

mapper = ObjectMapper.default(JsonModule())


def test_map():
  assert mapper.deserialize({'a': 22}, from_typing(t.Dict[str, int])) == {'a': 22}
