
import typing as t
import typing_extensions as te
from dataclasses import dataclass, field

from databind.core.annotations import alias
from databind.core.objectmapper import ObjectMapper
from databind.core.schema import Field, Schema
from databind.core.types import ConcreteType, ObjectType, OptionalType, from_typing
from .dataclass import dataclass_to_schema


def test_dataclass_to_schema_conversion():

  @dataclass
  class P:
    pass

  @dataclass
  class MyDataclass:
    a: int
    b: t.Optional[str] = field(default=None, metadata={'alias': 'balias'})
    c: te.Annotated[str, alias('calias')] = 42
    d: t.Optional[P] = None
    e: str = field(default='foobar', init=False)

  #schema = dataclass_to_schema(MyDataclass)
  type_ = ObjectMapper.default().adapt_type_hint(from_typing(MyDataclass))
  assert isinstance(type_, ObjectType)
  assert type_.schema == Schema(
    'MyDataclass',
    {
      'a': Field('a', ConcreteType(int)),
      'b': Field('b', OptionalType(ConcreteType(str)), [alias('balias')], default=None),
      'c': Field('c', ConcreteType(str), [alias('calias')], default=42),
      'd': Field('d', OptionalType(ObjectType(dataclass_to_schema(P))), default=None),
    },
    [],
    MyDataclass,
    type_.schema.composer
  )
