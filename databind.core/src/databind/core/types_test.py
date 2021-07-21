
import typing as t
import typing_extensions as te
from .types import *
from .types import _unpack_type_hint, find_generic_bases, populate_type_parameters

T = t.TypeVar('T')
K = t.TypeVar('K')
V = t.TypeVar('V')


def test_unpack_type_hint():
  assert _unpack_type_hint(t.List) == (list, [])
  assert _unpack_type_hint(t.List[int]) == (list, [int])
  assert _unpack_type_hint(t.Dict) == (dict, [])
  assert _unpack_type_hint(t.Dict[int, str]) == (dict, [int, str])

  class MyList(t.List[int]): pass
  assert _unpack_type_hint(MyList) == (MyList, [])

  class MyList(t.List[T]): pass
  assert _unpack_type_hint(MyList) == (MyList, [])
  assert _unpack_type_hint(MyList[int]) == (MyList, [int])

  class Foo(t.Generic[T]): pass
  class MyMulti(t.List[T], Foo[T]): pass
  assert _unpack_type_hint(MyMulti) == (MyMulti, [])
  assert _unpack_type_hint(MyMulti[int]) == (MyMulti, [int])


def test_find_generic_bases():
  assert find_generic_bases(t.List) == []
  assert find_generic_bases(t.List[int]) == []

  class MyList(t.List[int]): pass
  assert find_generic_bases(MyList) == [t.List[int]]

  class MyList(t.List[T]): pass
  assert find_generic_bases(MyList) == [t.List[T]]
  assert find_generic_bases(MyList[int]) == [t.List[int]]

  class Foo(t.Generic[T]): pass
  class MyMulti(t.List[T], Foo[T]): pass
  assert find_generic_bases(MyMulti) == [t.List[T], Foo[T], t.Generic[T]]
  assert find_generic_bases(MyMulti[int]) == [t.List[int], Foo[int], t.Generic[T]]

  class MyMore(t.List[int], t.Mapping[int, str]):
    pass
  assert find_generic_bases(MyMore) == [t.List[int], t.Mapping[int, str]]
  assert find_generic_bases(MyMore, t.List) == [t.List[int]]
  assert find_generic_bases(MyMore, t.Mapping) == [t.Mapping[int, str]]


def test_find_generic_bases_generic_subclass():
  T = t.TypeVar('T')
  class AnotherList(t.List[T]):
    pass
  assert find_generic_bases(AnotherList) == [t.List[T]]
  assert find_generic_bases(AnotherList[int]) == [t.List[int]]

  class AnotherSubclass(AnotherList[T]):
    pass
  assert find_generic_bases(AnotherSubclass) == [AnotherList[T], t.List[T]]
  assert find_generic_bases(AnotherSubclass[int]) == [AnotherList[int], t.List[int]]

  class MyList(AnotherList[int]):
    pass
  assert find_generic_bases(MyList) == [AnotherList[int], t.List[int]]


def test_find_generic_bases_docstring_example():
  class MyList(t.List[int]):
    ...
  class MyGenericList(t.List[T]):
    ...
  assert find_generic_bases(MyList) == [t.List[int]]
  assert find_generic_bases(MyGenericList) == [t.List[T]]
  assert find_generic_bases(MyGenericList[int]) == [t.List[int]]


def test_populate_type_parameters():
  assert populate_type_parameters(t.List, [T], [T], [int]) == t.List[int]
  assert populate_type_parameters(t.Mapping, [K, V], [V], [str]) == t.Mapping[K, str]


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
