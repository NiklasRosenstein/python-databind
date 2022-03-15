
import typing as t
from databind.core import ObjectMapper
from databind.core.types.adapter import TypeContext
from databind.json import JsonModule

mapper = ObjectMapper(JsonModule())


def test_map():
  assert mapper.deserialize({'a': 22}, TypeContext(mapper).adapt_type_hint(t.Dict[str, int])) == {'a': 22}
