
import typing as t
import typing_extensions as te
from .types import *
from .types import find_generic_bases

T = t.TypeVar('T')


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


def test_find_generic_bases():
  class MyList(t.List[int]):
    pass
  assert find_generic_bases(MyList) == [t.List[int]]
  class MyGenericList(t.List[T]):
    pass
  assert find_generic_bases(MyGenericList) == [t.List[T]]
  class MyMore(t.List[int], t.Mapping[int, str]):
    pass
  assert find_generic_bases(MyMore) == [t.List[int], t.Mapping[int, str]]
  assert find_generic_bases(MyMore, t.List) == [t.List[int]]
  assert find_generic_bases(MyMore, t.Mapping) == [t.Mapping[int, str]]


def test_custom_generic_subclass():
  class MyList(t.List[int]):
    pass
  assert from_typing(MyList) == ListType(ConcreteType(int), MyList)

  T = t.TypeVar('T')
  class AnotherList(t.List[T]):
    pass
  assert from_typing(AnotherList[int]) == ListType(ConcreteType(int), AnotherList)


def test_any():
  assert from_typing(t.Any) == ConcreteType(object)
