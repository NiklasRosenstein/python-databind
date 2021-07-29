
import typing as t
import typing_extensions as te
from dataclasses import dataclass, field

import pytest

from databind.core.annotations import alias
from databind.core.dataclasses import dataclass as ddataclass, field as dfield
from databind.core.objectmapper import ObjectMapper
from databind.core.types import Field, Schema, ConcreteType, ListType, ObjectType, OptionalType, from_typing
from .dataclasses import DataclassAdapter, dataclass_to_schema


def test_dataclass_adapter():
  @dataclass
  class MyDataclass:
    f: te.Annotated[int, 'foo']

  typ = DataclassAdapter().adapt_type_hint(ConcreteType(MyDataclass, ['foobar']))
  assert typ == ObjectType(dataclass_to_schema(MyDataclass), ['foobar'])
  assert typ.schema.fields['f'].type.annotations == ['foo']


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
      'c': Field('c', ConcreteType(str, [alias('calias')]), [], default=42),
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


@pytest.mark.skip("https://github.com/NiklasRosenstein/databind/issues/6")
def test_schema_from_generic_impl():
  T = t.TypeVar('T')
  @dataclass
  class Base(t.Generic[T]):
    items: t.List[T]
  @dataclass
  class Subclass(Base[int]):
    pass

  schema = dataclass_to_schema(Base[int])
  assert schema.fields == {
    'items': Field('items', ListType(ConcreteType(int)))
  }

  schema = dataclass_to_schema(Subclass)
  assert schema.fields == {
    'items': Field('items', ListType(ConcreteType(int)))
  }
