
import abc
import dataclasses
import typing as t
import typing_extensions as te
from databind.core.annotations import unionclass
from databind.core.annotations.typeinfo import typeinfo
from databind.core.objectmapper import ObjectMapper
from databind.core.types import from_typing
from databind.json import JsonModule, new_mapper

mapper = ObjectMapper.default(JsonModule())


def test_unionclass_from_annotated():
  MyUnion = te.Annotated[t.Union[int, str], unionclass({
    'int': int,
    'str': str
  }, name='MyUnion')]
  assert mapper.deserialize({'type': 'int', 'int': 42}, MyUnion) == 42
  assert mapper.deserialize({'type': 'str', 'str': 'foobar'}, MyUnion) == 'foobar'
  assert mapper.serialize(42, MyUnion) == {'type': 'int', 'int': 42}
  assert mapper.serialize('foobar', MyUnion) == {'type': 'str', 'str': 'foobar'}


def test_unionclass_object_type():

  @unionclass(style = unionclass.Style.flat)
  class Person(abc.ABC):
    @abc.abstractmethod
    def say_hello(self) -> str: ...

  @unionclass.subtype(Person)
  @dataclasses.dataclass
  class Student(Person):
    def say_hello(self) -> str:
      return 'Hi I study'

  @unionclass.subtype(Person)
  @dataclasses.dataclass
  @typeinfo(name = 'teacher')
  class Teacher(Person):
    def say_hello(self) -> str:
      return 'Hi I teach'

  assert mapper.deserialize({'type': 'Student'}, Person).say_hello() == 'Hi I study'
  assert mapper.deserialize({'type': 'teacher'}, Person).say_hello() == 'Hi I teach'


# ====
# Test that DyamicSubtypes/unionclass accepts a lambda function for lazy evaluation.

@dataclasses.dataclass
class B: pass

@dataclasses.dataclass
class A:
  other: te.Annotated['t.Union[B, C]', unionclass({
    'b': B,
    'c': lambda: C,
  })]

@dataclasses.dataclass
class C: pass

def test_dynamic_subtypes():
  assert new_mapper().deserialize({'other': {'type': 'b', 'b': {}}}, A) == A(B())
  assert new_mapper().deserialize({'other': {'type': 'c', 'c': {}}}, A) == A(C())
