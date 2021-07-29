
import typing as t
import typing_extensions as te
from dataclasses import dataclass

from databind.core.annotations.unionclass import unionclass, UnionConverter
from databind.core.types import from_typing
from databind.core.types.types import ListType
from databind.core.types.union import UnionType, DynamicSubtypes


def test_unionclass_adapter():

  @unionclass()
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


def test_unionclass_annotated_adapter():
  members = t.List[te.Annotated[t.Union[int, str], unionclass({
    'int': int,
    'str': str,
  })]]
  assert from_typing(members) == ListType(UnionType(DynamicSubtypes({
    'int': int,
    'str': str,
  }), python_type=t.Union[int, str]))
