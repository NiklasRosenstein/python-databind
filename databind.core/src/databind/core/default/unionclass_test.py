
import dataclasses

from databind.core.annotations.unionclass import unionclass
from databind.core.default.dataclass import DataclassAdapter
from databind.core.objectmapper import ObjectMapper
from databind.core.types import UnionType, from_typing
from databind.core.union import DynamicSubtypes
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
