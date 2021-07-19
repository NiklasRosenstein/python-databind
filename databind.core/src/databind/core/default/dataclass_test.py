
import typing as t
import typing_extensions as te
from dataclasses import dataclass

from databind.core.annotations import alias
from databind.core.schema import Field, Schema
from databind.core.types import ConcreteType, OptionalType
from .dataclass import dataclass_to_schema


def test_dataclass_to_schema_conversion():

  @dataclass
  class MyDataclass:
    a: int
    b: t.Optional[str] = None
    c: te.Annotated[str, alias('calias')] = 42

  schema = dataclass_to_schema(MyDataclass)
  assert schema == Schema(
    'MyDataclass',
    {
      'a': Field('a', ConcreteType(int), []),
      'b': Field('b', OptionalType(ConcreteType(str)), []),
      'c': Field('c', ConcreteType(str), (alias('calias'),)),
    },
    [],
    MyDataclass,
    schema.composer
  )
