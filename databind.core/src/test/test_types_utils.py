
import typing as t

from databind.core.types.utils import unpack_type_hint, find_generic_bases, populate_type_parameters

T = t.TypeVar('T')
K = t.TypeVar('K')
V = t.TypeVar('V')


def test_unpack_type_hint():
  assert unpack_type_hint(t.List) == (list, [])
  assert unpack_type_hint(t.List[int]) == (list, [int])
  assert unpack_type_hint(t.Dict) == (dict, [])
  assert unpack_type_hint(t.Dict[int, str]) == (dict, [int, str])

  class MyList(t.List[int]): pass
  assert unpack_type_hint(MyList) == (MyList, [])

  class MyList(t.List[T]): pass
  assert unpack_type_hint(MyList) == (MyList, [])
  assert unpack_type_hint(MyList[int]) == (MyList, [int])

  class Foo(t.Generic[T]): pass
  class MyMulti(t.List[T], Foo[T]): pass
  assert unpack_type_hint(MyMulti) == (MyMulti, [])
  assert unpack_type_hint(MyMulti[int]) == (MyMulti, [int])


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

  class MyMore(t.List[int], t.Mapping[int, str]):  # type: ignore
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

