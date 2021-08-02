
import typing as t
import typing_extensions as te
from dataclasses import dataclass
from databind.core.types import ConcreteType
from databind.core.types.types import ListType
from .union import DynamicSubtypes, ImportSubtypes, UnionConverter, UnionType, union
from . import from_typing, root


class Foobar: pass


def test_import_subtypes():
  assert ImportSubtypes().get_type_name(Foobar, root) == f'{__name__}.Foobar'
  assert ImportSubtypes().get_type_by_name(f'{__name__}.Foobar', root) == ConcreteType(Foobar)


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

  type_ = UnionConverter().convert_type_hint(from_typing(MyUnionType), UnionConverter())
  _check(type_)

  type_ = from_typing(from_typing(MyUnionType))
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
