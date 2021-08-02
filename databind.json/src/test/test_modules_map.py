
import typing as t
from databind.core.mapper import ObjectMapper
from databind.json import JsonModule

mapper = ObjectMapper(JsonModule())


def test_map():
  assert mapper.deserialize({'a': 22}, mapper.adapt_type_hint(t.Dict[str, int])) == {'a': 22}
