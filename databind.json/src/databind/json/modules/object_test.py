
import dataclasses
import pytest
from databind.core.objectmapper import ObjectMapper
from databind.json import JsonModule

mapper = ObjectMapper.default(JsonModule())


@pytest.mark.skip('not implemented')
def test_object_deserializer():

  @dataclasses.dataclass
  class Person:
    name: str
    age: int = 22

  assert mapper.serialize(Person('John'), Person) == {'name': 'John', 'age': 22}
  assert mapper.deserialize({'name': 'John', 'age': 40}, Person) == Person('John', 40)
  assert mapper.deserialize({'name': 'John'}, Person) == Person('John', 22)
