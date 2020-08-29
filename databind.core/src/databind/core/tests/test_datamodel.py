
from databind.core import *
from databind.core._union import StaticUnionResolver
from pytest import raises


def test_uniontype_decorator():
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

  assert isinstance(B.int, property)
  assert isinstance(B.str, property)

  assert B('int', 42).int == 42
  with raises(TypeError) as excinfo:
    B('int', 42).str
  assert str(excinfo.value) == f"{type_repr(B)}.str cannot be accessed if type == 'int'"

  b = B('int', 42)
  b.str = 'foo'
  assert b.type == 'str'


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
    a: int = field(default=0)
    b: int

  assert A(b=10) == A(0, 10)
  assert A(b=10, a=20) == A(20, 10)

  with raises(TypeError) as excinfo:
    A(42)
  assert str(excinfo.value) == "missing required argument 'b'"


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
