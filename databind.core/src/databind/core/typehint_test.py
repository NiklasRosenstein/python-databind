
import typing as t
import typing_extensions as te
from .typehint import *

def test_annotation_unpacking():
  assert Annotated(List(Annotated(Concrete(int), [42])), [43]).normalize() == \
    Annotated(List(Concrete(int)), [42, 43])


def test_from_typing():
  assert from_typing(int) == Concrete(int)
  assert from_typing(t.List[int]) == List(Concrete(int))
  assert from_typing(t.Mapping[str, t.Set[int]]) == Map(Concrete(str), Set(Concrete(int)), t.Mapping)
  assert from_typing(t.Dict[str, t.Set[int]]) == Map(Concrete(str), Set(Concrete(int)), t.Dict)
  assert from_typing(t.Optional[str]) == Optional(Concrete(str))
  assert from_typing(te.Annotated[t.Dict[te.Annotated[int, 42], te.Annotated[str, 'foo']], 'bar']).normalize() == \
    Annotated(Map(Concrete(int), Concrete(str)), [42, 'foo', 'bar'])
