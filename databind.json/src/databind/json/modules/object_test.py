
import dataclasses
import typing as t
import typing_extensions as te
from databind.core.annotations.enable_unknowns import enable_unknowns
import pytest
from databind.core import annotations as A
from databind.core.api import ConversionError
from databind.core.objectmapper import ObjectMapper
from databind.json import JsonModule

mapper = ObjectMapper.default(JsonModule())


def test_object_deserializer():

  @dataclasses.dataclass
  class Person:
    name: str
    age: int = 22

  assert mapper.serialize(Person('John'), Person) == {'name': 'John'}
  assert mapper.deserialize({'name': 'John', 'age': 40}, Person) == Person('John', 40)
  assert mapper.deserialize({'name': 'John'}, Person) == Person('John', 22)

  @dataclasses.dataclass
  class Nested:
    a: str
    b: Person

  assert mapper.serialize(Nested('foo', Person('John')), Nested) == {'a': 'foo', 'b': {'name': 'John'}}
  assert mapper.deserialize({'a': 'foo', 'b': {'name': 'John', 'age': 22}}, Nested) == Nested('foo', Person('John'))

  @dataclasses.dataclass
  class Flat:
    a: str
    b: te.Annotated[Person, A.fieldinfo(flat=True)]

  assert mapper.serialize(Flat('foo', Person('John')), Flat) == {'a': 'foo', 'name': 'John'}
  assert mapper.deserialize({'a': 'foo', 'name': 'John', 'age': 22}, Flat) == Flat('foo', Person('John'))


def test_object_optional_field():

  @dataclasses.dataclass
  class Person:
    name: str
    age: t.Optional[int] = None

  assert mapper.serialize(Person('John', 22), Person) == {'name': 'John', 'age': 22}
  assert mapper.serialize(Person('John'), Person) == {'name': 'John'}

  @dataclasses.dataclass
  class SomePerson:
    person: t.Optional[Person]

  assert mapper.serialize(SomePerson(Person('John')), SomePerson) == {'person': {'name': 'John'}}
  assert mapper.deserialize({'person': {'name': 'John'}}, SomePerson) == SomePerson(Person('John'))


def test_unknown_keys():

  @dataclasses.dataclass
  class Person:
    name: str

  with pytest.raises(ConversionError) as excinfo:
    mapper.deserialize({'name': 'John', 'age': 22}, Person)
  assert str(excinfo.value) == "[None] ($ ObjectType(Person)): unknown keys found while deserializing ObjectType(Person): {'age'}"

  unknown_keys = []
  unknowns = enable_unknowns(callback=lambda ctx, keys: unknown_keys.extend(keys))
  mapper.deserialize({'name': 'John', 'age': 22}, Person, settings=[unknowns])
  assert unknown_keys == ['age']


def test_deserialize_dataclass_field_as():

  @dataclasses.dataclass
  class One:
    pass

  class Two(One):
    pass

  @dataclasses.dataclass
  class Three:
    one: te.Annotated[One, A.typeinfo(deserialize_as=Two)]

  assert mapper.deserialize({'one': {}}, Three) == Three(Two())
  assert mapper.serialize(Three(Two()), Three) == {'one': {}}
