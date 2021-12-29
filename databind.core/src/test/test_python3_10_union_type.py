
import dataclasses
import textwrap
import types
import typing as t
import pytest
from databind.core import ObjectMapper
from databind.core.types.schema import dataclass_to_schema

if hasattr(types, 'UnionType'):
  exec(textwrap.dedent('''
  @dataclasses.dataclass
  class Person1:
    name: str | None
    age: int
  '''))

@dataclasses.dataclass
class Person2:
  name: t.Optional[str]
  age: int

@pytest.mark.skipif(not hasattr(types, 'UnionType'), reason='need types.UnionType (Python >= 3.10)')
def test_person1():
  mapper = ObjectMapper()
  assert dataclass_to_schema(Person1, mapper).fields == dataclass_to_schema(Person2, mapper).fields
