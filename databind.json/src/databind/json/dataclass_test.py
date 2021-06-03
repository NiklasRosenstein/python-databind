
import typing as t
import typing_extensions as te
from dataclasses import dataclass

from databind.core.schema import Field, Schema
from databind.core.typehint import Concrete, Optional
from .dataclass import dataclass_to_schema
from databind.core.annotations import alias


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
      'a': Field('a', Concrete(int), []),
      'b': Field('b', Optional(Concrete(str)), []),
      'c': Field('c', Concrete(str), (alias('calias'),)),
    },
    MyDataclass,
    schema.composer
  )
