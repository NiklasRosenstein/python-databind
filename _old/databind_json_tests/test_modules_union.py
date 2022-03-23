# type: ignore

import abc
import dataclasses
import typing as t
import typing_extensions as te
from databind.core import annotations as A
from databind.json import mapper


def test_unionclass_from_annotated():
  MyUnion = te.Annotated[t.Union[int, str], A.union({
    'int': int,
    'str': str
  }, name='MyUnion')]
  assert mapper().deserialize({'type': 'int', 'int': 42}, MyUnion) == 42
  assert mapper().deserialize({'type': 'str', 'str': 'foobar'}, MyUnion) == 'foobar'
  assert mapper().serialize(42, MyUnion) == {'type': 'int', 'int': 42}
  assert mapper().serialize('foobar', MyUnion) == {'type': 'str', 'str': 'foobar'}


def test_unionclass_object_type():

  @A.union(style = A.union.Style.flat)
  class Person(abc.ABC):
    @abc.abstractmethod
    def say_hello(self) -> str: ...

  @A.union.subtype(Person)
  @dataclasses.dataclass
  class Student(Person):
    def say_hello(self) -> str:
      return 'Hi I study'

  @A.union.subtype(Person)
  @dataclasses.dataclass
  @A.typeinfo(name = 'teacher')
  class Teacher(Person):
    def say_hello(self) -> str:
      return 'Hi I teach'

  assert mapper().deserialize({'type': 'Student'}, Person).say_hello() == 'Hi I study'
  assert mapper().deserialize({'type': 'teacher'}, Person).say_hello() == 'Hi I teach'


def test_union_keyed():

  @A.union(style = A.union.Style.keyed)
  class Person(abc.ABC):
    @abc.abstractmethod
    def say_hello(self) -> str: ...

  @A.union.subtype(Person)
  @dataclasses.dataclass
  class Student(Person):
    name: str
    def say_hello(self) -> str:
      return f'Hi I study and my name is {self.name}'

  @A.union.subtype(Person)
  @dataclasses.dataclass
  @A.typeinfo(name = 'teacher')
  class Teacher(Person):
    def say_hello(self) -> str:
      return 'Hi I teach'

  assert mapper().deserialize({'Student': {'name': 'John'}}, Person).say_hello() == 'Hi I study and my name is John'
  assert mapper().deserialize({'teacher': {}}, Person).say_hello() == 'Hi I teach'

# ====
# Test that DyamicSubtypes/A.union accepts a lambda function for lazy evaluation.

@dataclasses.dataclass
class Bcls: pass

@dataclasses.dataclass
class Acls:
  other: te.Annotated['t.Union[Bcls, Ccls]', A.union({
    'b': Bcls,
    'c': lambda: Ccls,
  })]

@dataclasses.dataclass
class Ccls: pass

def test_dynamic_subtypes():
  assert mapper().deserialize({'other': {'type': 'b', 'b': {}}}, Acls) == Acls(Bcls())
  assert mapper().deserialize({'other': {'type': 'c', 'c': {}}}, Acls) == Acls(Ccls())


def test_file_content_api():

  @dataclasses.dataclass
  class FileContentMarkdown:
    markdown: str

  @dataclasses.dataclass
  class FileContentMedia:
    media: bytes

  FileContent = te.Annotated[t.Union[
    FileContentMarkdown,
    FileContentMedia,
  ], A.union({
    'markdown': FileContentMarkdown,
    'media': FileContentMedia,
  }, style=A.union.Style.flat)]

  assert mapper().serialize(FileContentMarkdown('Hello'), FileContent) == {'type': 'markdown', 'markdown': 'Hello'}
  assert mapper().deserialize({'type': 'markdown', 'markdown': 'Hello'}, FileContent) == FileContentMarkdown('Hello')
  assert mapper().serialize(FileContentMedia(b'Hello'), FileContent) == {'type': 'media', 'media': 'SGVsbG8='}
  assert mapper().deserialize({'type': 'media', 'media': 'SGVsbG8='}, FileContent) == FileContentMedia(b'Hello')
