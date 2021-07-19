
import dataclasses
import typing_extensions as te
from databind.core import annotations as A
from databind.core.objectmapper import ObjectMapper
from databind.json import JsonModule

mapper = ObjectMapper.default(JsonModule())


def test_object_deserializer():

  @dataclasses.dataclass
  class Person:
    name: str
    age: int = 22

  assert mapper.serialize(Person('John'), Person) == {'name': 'John', 'age': 22}
  assert mapper.deserialize({'name': 'John', 'age': 40}, Person) == Person('John', 40)
  assert mapper.deserialize({'name': 'John'}, Person) == Person('John', 22)

  @dataclasses.dataclass
  class Nested:
    a: str
    b: Person

  assert mapper.serialize(Nested('foo', Person('John')), Nested) == {'a': 'foo', 'b': {'name': 'John', 'age': 22}}
  assert mapper.deserialize({'a': 'foo', 'b': {'name': 'John', 'age': 22}}, Nested) == Nested('foo', Person('John'))

  @dataclasses.dataclass
  class Flat:
    a: str
    b: te.Annotated[Person, A.fieldinfo(flat=True)]

  assert mapper.serialize(Flat('foo', Person('John')), Flat) == {'a': 'foo', 'name': 'John', 'age': 22}
  assert mapper.deserialize({'a': 'foo', 'name': 'John', 'age': 22}, Flat) == Flat('foo', Person('John'))
