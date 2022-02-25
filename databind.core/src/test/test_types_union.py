# type: ignore

import typing as t
import typing_extensions as te
from databind.core.types.adapter import TypeContext
from dataclasses import dataclass
from databind.core import ObjectMapper, ConcreteType, ListType, UnionAdapter, UnionType
from databind.core.annotations import union

mapper = ObjectMapper()
from_typing = TypeContext(mapper).adapt_type_hint


class Foobar: pass


def test_import_subtypes():
  assert union.Subtypes.import_().get_type_name(Foobar, mapper) == f'{__name__}.Foobar'
  assert union.Subtypes.import_().get_type_by_name(f'{__name__}.Foobar', mapper) == ConcreteType(Foobar)


def test_union_adapter():

  @union()
  @dataclass
  class MyUnionType:
    pass

  def _check(type_: UnionType):
    assert isinstance(type_, UnionType)
    assert isinstance(type_.subtypes, union.Subtypes.dynamic)
    assert type_.style == None
    assert type_.discriminator_key == None

  type_ = TypeContext(UnionAdapter()).adapt_type_hint(ConcreteType(MyUnionType))
  _check(type_)

  type_ = from_typing(MyUnionType)
  _check(type_)


def test_union_annotated_adapter():
  members = t.List[te.Annotated[t.Union[int, str], union({
    'int': int,
    'str': str,
  })]]
  assert from_typing(members) == ListType(UnionType(union.Subtypes.dynamic({
    'int': int,
    'str': str,
  }), python_type=t.Union[int, str]))


def test_non_dataclass_union_annotated_type():
  class Strategy:
    pass

  class PriceChangeStrategy(Strategy):
    pass

  ann = union({ 'pc': PriceChangeStrategy }, style=union.Style.flat)
  type_ = from_typing(te.Annotated[Strategy, ann])
  assert type_.annotations == []
  assert isinstance(type_, UnionType)
