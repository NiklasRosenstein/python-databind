
import typing as t
from .typehint import *


def test_from_typing():
  assert from_typing(int) == Concrete(int)
  assert from_typing(t.List[int]) == List(Concrete(int))
  assert from_typing(t.Mapping[str, t.Set[int]]) == Map(Concrete(str), Set(Concrete(int)), t.Mapping)
  assert from_typing(t.Dict[str, t.Set[int]]) == Map(Concrete(str), Set(Concrete(int)), t.Dict)
