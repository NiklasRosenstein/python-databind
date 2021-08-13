# type: ignore

import dataclasses
import typing as t
import typing_extensions as te

import pytest

from databind.core import annotations as A, ConversionError, ObjectMapper
from databind.json import JsonModule

mapper = ObjectMapper(JsonModule())


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
  assert str(excinfo.value) == "[None] ($ ObjectType(test_modules_object.test_unknown_keys.<locals>.Person)): "\
      "unknown keys found while deserializing ObjectType(test_modules_object.test_unknown_keys.<locals>.Person): {'age'}"

  unknown_keys = []
  unknowns = A.enable_unknowns(callback=lambda ctx, keys: unknown_keys.extend(keys))
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


def test_map_remainders():

  @dataclasses.dataclass
  class Foo:
    pass

  @dataclasses.dataclass
  class Config:
    port: int
    rest: te.Annotated[t.Dict[str, t.Union[str, int, Foo]], A.fieldinfo(flat=True)]

  payload = {'port': 42, 'foo': 'bar', 'spam': 0, 'baz': {}}
  cfg = mapper.deserialize(payload, Config)
  assert cfg == Config(42, {'foo': 'bar', 'spam': 0, 'baz': Foo()})
  assert mapper.serialize(cfg, Config) == payload

  with pytest.raises(ConversionError) as excinfo:
    mapper.serialize(Config(42, {'port': 'bar'}), Config)
  assert str(excinfo.value) == "[None] ($ ObjectType(test_modules_object.test_map_remainders.<locals>.Config)): key 'port' of remainder field 'rest' cannot be exploded into resulting JSON object because of a conflict."
