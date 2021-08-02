
import typing as t
import typing_extensions as te
from databind.core.types import *

T = t.TypeVar('T')


def test_from_typing():
  assert from_typing(int) == ConcreteType(int)
  assert from_typing(t.Mapping[str, t.Set[int]]) == MapType(ConcreteType(str), SetType(ConcreteType(int)), t.Mapping)

  t1 = from_typing(te.Annotated[t.List[te.Annotated[int, 42]], 'foobar'])
  assert t1 == ListType(ConcreteType(int, annotations=[42]), annotations=['foobar'])
  assert t1 == t1.visit(lambda x: x)

  t1 = from_typing(te.Annotated[t.Dict[str, t.Set[int]], 'foobar'])
  assert t1 == MapType(ConcreteType(str), SetType(ConcreteType(int)), t.Dict, annotations=['foobar'])
  assert t1.visit(lambda x: x) == t1

  t1 = from_typing(te.Annotated[t.Optional[str], 'foobar'])
  assert t1 == OptionalType(ConcreteType(str), annotations=['foobar'])
  assert t1.visit(lambda x: x) == t1

  t1 = from_typing(te.Annotated[int, 42])
  assert t1 == ConcreteType(int, annotations=[42])
  assert t1 != ConcreteType(int, annotations=[40])
  assert t1.visit(lambda x: x) == t1

  t1 = from_typing(te.Annotated[t.Dict[te.Annotated[int, 42], te.Annotated[str, 'foo']], 'bar'])
  assert t1 == MapType(ConcreteType(int, [42]), ConcreteType(str, ['foo']), annotations=['bar'])
  assert t1.visit(lambda x: x) == t1


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
