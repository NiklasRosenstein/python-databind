
import dataclasses
from databind.core.objectmapper import ObjectMapper
from databind.json import JsonModule

mapper = ObjectMapper.default(JsonModule())


def test_unionclass_deserializer():
  pass
