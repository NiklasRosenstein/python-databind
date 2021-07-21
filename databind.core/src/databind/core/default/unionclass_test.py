
import dataclasses
import typing as t
import typing_extensions as te

from databind.core.annotations.unionclass import unionclass
from databind.core.objectmapper import ObjectMapper
from databind.core.types import ListType, UnionType, from_typing
from databind.core.union import DynamicSubtypes
from .dataclasses import DataclassAdapter
from .unionclass import UnionclassAdapter


def test_unionclass_adapter():

  @unionclass()
  @dataclasses.dataclass
  class MyUnionType:
    pass

  def _check(type_: UnionType):
    assert isinstance(type_, UnionType)
    assert isinstance(type_.subtypes, DynamicSubtypes)
    assert type_.style == None
    assert type_.discriminator_key == None

  type_ = UnionclassAdapter().adapt_type_hint(from_typing(MyUnionType))
  _check(type_)

  mapper = ObjectMapper(UnionclassAdapter(), DataclassAdapter())
  _check(mapper.adapt_type_hint(from_typing(MyUnionType)))

  mapper = ObjectMapper(DataclassAdapter(), UnionclassAdapter())
  _check(mapper.adapt_type_hint(from_typing(MyUnionType)))


def test_unionclass_annotated_adapter():
  members = t.List[te.Annotated[t.Union[int, str], unionclass({
    'int': int,
    'str': str,
  })]]
  assert ObjectMapper.default().adapt_type_hint(from_typing(members)) == ListType(UnionType(DynamicSubtypes({
    'int': int,
    'str': str,
  }), python_type=t.Union[int, str]))
