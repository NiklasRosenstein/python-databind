
import typing as t
import typing_extensions as te
from dataclasses import dataclass, field
from databind.core.dataclasses import dataclass as ddataclass, field as dfield

from databind.core.annotations import alias
from databind.core.objectmapper import ObjectMapper
from databind.core.schema import Field, Schema
from databind.core.types import ConcreteType, ListType, ObjectType, OptionalType, from_typing
from .dataclasses import dataclass_to_schema


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
  )


def test_dataclass_field_with_custom_generic_subclass():

  T = t.TypeVar('T')
  class MyList(t.List[T]):
    pass

  @dataclass
  class Data:
    vals: MyList[int]

  type_ = ObjectMapper.default().adapt_type_hint(from_typing(Data))
  assert isinstance(type_, ObjectType)
  assert type_.schema == Schema(
    'Data',
    {
      'vals': Field('vals', ListType(ConcreteType(int), MyList))
    },
    [],
    Data)


def test_databind_dataclass_field_annotations():

  @ddataclass
  class MyClass:
    f: int = dfield(annotations=['foobar'])

  type_ = ObjectMapper.default().adapt_type_hint(from_typing(MyClass))
  assert isinstance(type_, ObjectType)
  assert type_.schema == Schema(
    'MyClass',
    {
      'f': Field('f', ConcreteType(int), ['foobar']),
    },
    [],
    MyClass
  )
