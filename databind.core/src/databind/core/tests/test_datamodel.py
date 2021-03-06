
import abc
from databind.core import *
from databind.core._union import InterfaceUnionResolver, StaticUnionResolver
from pytest import raises


def test_uniontype_with_static_resolver():
  @uniontype({
    'int': int,
    'str': str,
  })
  class A:
    pass

  def _a_checks(A):
    assert hasattr(A, '__databind_metadata__')
    assert isinstance(A.__databind_metadata__, UnionMetadata)
    assert UnionMetadata.for_type(A) == UnionMetadata(resolver=StaticUnionResolver({
      'int': int,
      'str': str,
    }))

  _a_checks(A)

  @uniontype
  class A:
    int: int
    str: str

  _a_checks(A)

  with raises(TypeError) as excinfo:
    A()
  assert str(excinfo.value) == f'non-container @uniontype {type_repr(A)} cannot be constructed directly'

  @uniontype(container=True)
  class B:
    int: int
    str: str

  metadata = B.__databind_metadata__
  assert isinstance(metadata, UnionMetadata)

  assert B(int=42).int == 42
  with raises(TypeError) as excinfo:
    B(int=42).str
  assert str(excinfo.value) == f"B.str cannot be accessed when type is .int"

  b = B(int=42)
  b.str = 'foo'
  assert b.type == 'str'

  @uniontype(container=True)
  class C(B):
    number: int
    float: float

  assert B(int=42) == B(int=42)
  assert B(int=42) != B(int=43)
  assert B(int=42) == C(int=42)
  assert B(int=42) != C(number=42)


def test_interface_and_implementation_decorator():
  @interface
  class BaseClass(metaclass=abc.ABCMeta):
    pass

  @implementation('a')
  class ASubclass(BaseClass):
    pass

  @implementation('b', BaseClass)
  class BNotSubclass:
    pass

  assert UnionMetadata.for_type(BaseClass) == UnionMetadata(resolver=InterfaceUnionResolver({
    'a': ASubclass,
    'b': BNotSubclass,
  }))

  @uniontype
  class AnotherBaseClass:
    pass

  with raises(RuntimeError) as excinfo:
    @implementation('c')
    class C(AnotherBaseClass):
      pass
  assert str(excinfo.value) == '@imlpementation() can only be used if at least one base is decorated with @interface() and uses an InterfaceUnionResolver'


  with raises(RuntimeError) as excinfo:
    @implementation('c', AnotherBaseClass)
    class C(AnotherBaseClass):
      pass
  assert str(excinfo.value) == f'@implementation(for_={type_repr(AnotherBaseClass)}) can only be used if the for_ argument is a class decorated with @interface() and uses an InterfaceUnionResolver'


def test_datamodel_decorator():
  @datamodel
  class A:
    pass

  assert hasattr(A, '__databind_metadata__')
  assert isinstance(A.__databind_metadata__, ModelMetadata)
  assert A.__databind_metadata__.kwonly == False
  assert ModelMetadata.for_type(A) == ModelMetadata()

  @datamodel(kwonly=True)
  class B:
    field: int

  assert hasattr(B, '__databind_metadata__')
  assert isinstance(B.__databind_metadata__, ModelMetadata)
  assert B.__databind_metadata__.kwonly == True
  assert ModelMetadata.for_type(B) == ModelMetadata(kwonly=True)

  with raises(TypeError) as excinfo:
    B(42)
  assert str(excinfo.value) == '__init__() takes 1 positional argument but 2 were given'

  assert B(field=42).field == 42


def test_datamodel_mixed_order_default_arguments():
  """
  The #@datamodel() decorator overrides the behavior of the underlying #@dataclass() decorator
  and allows for non-default arguments to follow default arguments.
  """

  @datamodel
  class A:
    a: int

  @datamodel
  class B(A):
    b: int = field(default=0)

  assert not hasattr(B, 'a')
  assert B.b == 0

  assert B(a=10) == B(10, 0)
  assert B(b=10, a=20) == B(20, 10)

  with raises(TypeError) as excinfo:
    B(b=10)
  assert str(excinfo.value) == "missing required argument 'a'"


def test_datamodel_multiple_inheritance():
  @datamodel
  class A:
    a: int

  @datamodel
  class B:
    b: str

  @datamodel
  class C(B, A):
    c: float

  assert C(42, 'foo', 4.0) == C(a=42, b='foo', c=4.0)

  @datamodel
  class D(A, B):
    d: float

  assert D('foo', 42, 4.0) == D(a=42, b='foo', d=4.0)


def test_FieldMetadata_constructor():
  assert FieldMetadata().derived == False
  assert FieldMetadata(raw=True).derived == True


def test_field_function():
  f = field(default=32, required=True)
  assert f.default == 32
  assert FieldMetadata.for_field(f) == FieldMetadata(required=True, _owning_field=f, metadata=f.metadata)
  assert FieldMetadata.for_field(f).required == True

  f = field(formats=['%Y-%m-%d'])
  assert FieldMetadata.for_field(f) == FieldMetadata(formats=['%Y-%m-%d'], _owning_field=f, metadata=f.metadata)

  f = field()
  assert FieldMetadata.for_field(f) == FieldMetadata(formats=[], _owning_field=f, metadata=f.metadata)
