# type: ignore

import sys
import typing as t
import typing_extensions as te
import pytest
from databind.core.types.types import *
from databind.core.mapper.objectmapper import ObjectMapper

T = t.TypeVar('T')
mapper = ObjectMapper()
from_typing = mapper.adapt_type_hint

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
  """
  Tests if custom generic subclasses of for example #t.List are understood as such.
  """

  class MyList(t.List[int]):
    pass
  assert from_typing(MyList) == ListType(ConcreteType(int), MyList)

  T = t.TypeVar('T')
  class AnotherList(t.List[T]):
    pass
  assert from_typing(AnotherList[int]) == ListType(ConcreteType(int), AnotherList)

  class GenericBase(t.Generic[T]):
    pass
  class Subclass(GenericBase[int], t.List[int]):
    pass
  assert from_typing(Subclass) == ListType(ConcreteType(int), Subclass)


@pytest.mark.skipif(sys.version_info < (3, 9), reason='PEP585 requires Python 3.9 or higher')
def test_pep585_generic_aliases():
  assert from_typing(dict[str, set[int]]) == MapType(ConcreteType(str), SetType(ConcreteType(int)), t.Dict)

  t1 = from_typing(te.Annotated[list[te.Annotated[int, 42]], 'foobar'])
  assert t1 == ListType(ConcreteType(int, annotations=[42]), annotations=['foobar'])
  assert t1 == t1.visit(lambda x: x)

  t1 = from_typing(te.Annotated[dict[str, set[int]], 'foobar'])
  assert t1 == MapType(ConcreteType(str), SetType(ConcreteType(int)), t.Dict, annotations=['foobar'])
  assert t1.visit(lambda x: x) == t1


@pytest.mark.skipif(sys.version_info < (3, 9), reason='PEP585 requires Python 3.9 or higher')
def test_pep585_generic_aliases_with_forward_references():
  with pytest.raises(ValueError) as excinfo:
    from_typing(dict['str', set[int]])
  assert str(excinfo.value) == "encountered forward reference in PEP585 generic `dict['str', set[int]]` but no ForwardReferenceResolver is supplied"


@pytest.mark.skipif(sys.version_info < (3, 10), reason='PEP604 requires Python 3.10 or higher')
def test_pep604_union_types():
  t1 = from_typing(te.Annotated[str | None, 'foobar'])
  assert t1 == OptionalType(ConcreteType(str), annotations=['foobar'])
  assert t1.visit(lambda x: x) == t1

  t1 = from_typing(int | str)
  assert t1 == ImplicitUnionType((ConcreteType(int), ConcreteType(str)))
  assert t1.visit(lambda x: x) == t1


def test_any():
  assert from_typing(t.Any) == ConcreteType(object)
