
import typing as t
import typing_extensions as te
from dataclasses import dataclass
from databind.core.mapper import ObjectMapper
from databind.core.types import ConcreteType, ListType
from databind.core.types.union import DynamicSubtypes, ImportSubtypes, UnionAdapter, UnionType, union

mapper = ObjectMapper()
from_typing = mapper.adapt_type_hint


class Foobar: pass


def test_import_subtypes():
  assert ImportSubtypes().get_type_name(Foobar, mapper) == f'{__name__}.Foobar'
  assert ImportSubtypes().get_type_by_name(f'{__name__}.Foobar', mapper) == ConcreteType(Foobar)


def test_union_adapter():

  @union()
  @dataclass
  class MyUnionType:
    pass

  def _check(type_: UnionType):
    assert isinstance(type_, UnionType)
    assert isinstance(type_.subtypes, DynamicSubtypes)
    assert type_.style == None
    assert type_.discriminator_key == None

  type_ = UnionAdapter().adapt_type_hint(ConcreteType(MyUnionType))
  _check(type_)

  type_ = from_typing(MyUnionType)
  print(type_)
  _check(type_)


def test_union_annotated_adapter():
  members = t.List[te.Annotated[t.Union[int, str], union({
    'int': int,
    'str': str,
  })]]
  assert from_typing(members) == ListType(UnionType(DynamicSubtypes({
    'int': int,
    'str': str,
  }), python_type=t.Union[int, str]))
