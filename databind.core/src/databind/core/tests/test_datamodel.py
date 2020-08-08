
from databind.core._datamodel import *
from databind.core._union import StaticUnionResolver
from pytest import raises


def test_uniontype_decorator():
  @uniontype({
    'int': int,
    'str': str,
  })
  class A:
    pass

  assert hasattr(A, '__databind_metadata__')
  assert isinstance(A.__databind_metadata__, UnionMetadata)
  assert UnionMetadata.for_type(A) == UnionMetadata(resolver=StaticUnionResolver({
    'int': int,
    'str': str,
  }))


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


def test_FieldMetadata_constructor():
  assert FieldMetadata().derived == False
  assert FieldMetadata(raw=True).derived == True


def test_field_function():
  f = field(default=32, required=True)
  assert f.default == 32
  assert FieldMetadata.for_field(f) == FieldMetadata(required=True)
  assert FieldMetadata.for_field(f).required == True

  f = field(formats=['%Y-%m-%d'])
  assert FieldMetadata.for_field(f) == FieldMetadata(formats=['%Y-%m-%d'])

  f = field()
  assert FieldMetadata.for_field(f) == FieldMetadata(formats=[])
