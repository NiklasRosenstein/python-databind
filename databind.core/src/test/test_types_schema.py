
import dataclasses
import typing as t
import typing_extensions as te
import pytest

from databind.core.annotations import alias, fieldinfo
from databind.core.dataclasses import dataclass as ddataclass, field as dfield
from databind.core.mapper import ObjectMapper
from databind.core.types import Field, Schema, ConcreteType, ListType, ObjectType, OptionalType
from databind.core.types.schema import SchemaDefinitionError, ObjectType, DataclassAdapter, dataclass_to_schema

mapper = ObjectMapper()
from_typing = mapper.adapt_type_hint


def test_schema_flat_fields_check():

  @dataclasses.dataclass
  class A:
    foo: str
    bar: str

  assert isinstance(from_typing(A), ObjectType)

  @dataclasses.dataclass
  class B:
    foo: str
    a: te.Annotated[A, fieldinfo(flat=True)]  # Field cannot be flat because of conflicting members "foo".

  with pytest.raises(SchemaDefinitionError) as excinfo:
    assert isinstance(from_typing(B), ObjectType)
  assert '($.foo, $.a.foo)' in str(excinfo)


def test_dataclass_adapter():
  @dataclasses.dataclass
  class MyDataclass:
    f: te.Annotated[int, 'foo']

  typ = DataclassAdapter().adapt_type_hint(ConcreteType(MyDataclass, ['foobar']), mapper)
  assert typ == ObjectType(dataclass_to_schema(MyDataclass, mapper), ['foobar'])
  assert typ.schema.fields['f'].type.annotations == ['foo']


def test_dataclass_to_schema_conversion():

  @dataclasses.dataclass
  class P:
    pass

  @dataclasses.dataclass
  class MyDataclass:
    a: int
    b: t.Optional[str] = dataclasses.field(default=None, metadata={'alias': 'balias'})
    c: te.Annotated[str, alias('calias')] = 42
    d: t.Optional[P] = None
    e: str = dataclasses.field(default='foobar', init=False)

  #schema = dataclass_to_schema(MyDataclass)
  type_ = from_typing(MyDataclass)
  assert isinstance(type_, ObjectType)
  assert type_.schema == Schema(
    'MyDataclass',
    {
      'a': Field('a', ConcreteType(int)),
      'b': Field('b', OptionalType(ConcreteType(str)), [alias('balias')], default=None),
      'c': Field('c', ConcreteType(str, [alias('calias')]), [], default=42),
      'd': Field('d', OptionalType(ObjectType(dataclass_to_schema(P, mapper))), default=None),
    },
    [],
    MyDataclass,
  )


def test_dataclass_field_with_custom_generic_subclass():

  T = t.TypeVar('T')
  class MyList(t.List[T]):
    pass

  @dataclasses.dataclass
  class Data:
    vals: MyList[int]

  type_ = from_typing(Data)
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

  type_ = from_typing(MyClass)
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

  schema = dataclass_to_schema(Base[int], mapper)
  assert schema.fields == {
    'items': Field('items', ListType(ConcreteType(int)))
  }

  schema = dataclass_to_schema(Subclass, mapper)
  assert schema.fields == {
    'items': Field('items', ListType(ConcreteType(int)))
  }
