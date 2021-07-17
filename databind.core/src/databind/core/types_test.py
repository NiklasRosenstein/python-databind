
import typing as t
import typing_extensions as te
from .types import *

def test_annotation_unpacking():
  assert AnnotatedType(ListType(AnnotatedType(ConcreteType(int), [42])), [43]).normalize() == \
    AnnotatedType(ListType(ConcreteType(int)), [42, 43])


def test_from_typing():
  assert from_typing(int) == ConcreteType(int)
  assert from_typing(t.List[int]) == ListType(ConcreteType(int))
  assert from_typing(t.Mapping[str, t.Set[int]]) == MapType(ConcreteType(str), SetType(ConcreteType(int)), t.Mapping)
  assert from_typing(t.Dict[str, t.Set[int]]) == MapType(ConcreteType(str), SetType(ConcreteType(int)), t.Dict)
  assert from_typing(t.Optional[str]) == OptionalType(ConcreteType(str))
  assert from_typing(te.Annotated[t.Dict[te.Annotated[int, 42], te.Annotated[str, 'foo']], 'bar']).normalize() == \
    AnnotatedType(MapType(ConcreteType(int), ConcreteType(str)), [42, 'foo', 'bar'])
