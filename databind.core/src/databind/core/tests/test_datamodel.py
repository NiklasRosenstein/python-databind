
from databind.core._datamodel import *
from databind.core._union import StaticUnionResolver


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
    pass

  assert hasattr(B, '__databind_metadata__')
  assert isinstance(B.__databind_metadata__, ModelMetadata)
  assert B.__databind_metadata__.kwonly == True
  assert ModelMetadata.for_type(B) == ModelMetadata(kwonly=True)


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
