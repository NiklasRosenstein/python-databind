
import decimal
import enum
from typing import Dict, List, Optional, Union
from databind.core import *
from databind.json import *
from pytest import raises


def test_int_converter():
  assert from_json(int, 42) == 42
  assert to_json(42) == 42
  with raises(ConversionTypeError) as excinfo:
    from_json(int, "foo")
  assert str(excinfo.value) == '$: expected integer, got str'


def test_decimal_converter():

  # Test with default decimal context.
  assert from_json(decimal.Decimal, "42.51532") == decimal.Decimal("42.51532")
  assert to_json(decimal.Decimal("124.532525")) == "124.532525"

  # Test with custom decimal context.
  ctx = decimal.Context(prec=5)
  assert from_json(
    decimal.Decimal,
    "124.24124325001",
    field_metadata=FieldMetadata(formats=[ctx])
  ) == decimal.Decimal("124.24")
  assert to_json(
    decimal.Decimal("124.152542"),
    field_metadata=FieldMetadata(formats=[ctx])
  ) == "124.15"

  # Test with global custom decimal context.
  new_registry = Registry(registry)
  new_registry.update_options(decimal.Decimal, {'context': ctx})
  assert from_json(
    decimal.Decimal,
    "124.24124325001",
    registry=new_registry,
  ) == decimal.Decimal("124.24")
  assert to_json(
    decimal.Decimal("124.152542"),
    registry=new_registry,
  ) == "124.15"


def test_enum_converter():
  class Pet(enum.Enum):
    CAT = enum.auto()
    DOG = enum.auto()

  assert from_json(Pet, 'CAT') == Pet.CAT
  assert from_json(Pet, 'DOG') == Pet.DOG
  with raises(ConversionValueError) as excinfo:
    from_json(Pet, 'BIRD')
  assert str(excinfo.value) == f"$: invalid value for enum {type_repr(Pet)}: 'BIRD'"
  with raises(ConversionTypeError) as excinfo:
    from_json(Pet, 42)
  assert str(excinfo.value) == f"$: expected {type_repr(Pet)} (as string), got int"

  assert to_json(Pet.CAT) == 'CAT'
  assert to_json(Pet.DOG) == 'DOG'
  with raises(ConversionTypeError) as excinfo:
    to_json(42, Pet)
  assert str(excinfo.value) == f"$: expected {type_repr(Pet)}, got int"


def test_optional_converter():
  assert from_json(Optional[int], None) == None
  assert from_json(Optional[int], 242) == 242
  with raises(ConversionTypeError) as excinfo:
    from_json(Optional[int], "foo")
  assert str(excinfo.value) == '$: expected typing.Union[int, NoneType], got str'

  assert to_json(None, Optional[int]) == None
  assert to_json(242, Optional[int]) == 242
  with raises(ConversionTypeError) as excinfo:
    to_json("foo", Optional[int])
  assert str(excinfo.value) == '$: expected typing.Union[int, NoneType], got str'


def test_mixtype_converter():
  assert from_json(Union[int, str], 242) == 242
  assert from_json(Union[int, str], "foo") == "foo"
  with raises(ConversionTypeError) as excinfo:
    from_json(Union[int, str], 342.324)
  assert str(excinfo.value) == "$: expected typing.Union[int, str], got float"


def test_array_converter():
  assert from_json(List[int], [1, 2, 3]) == [1, 2, 3]
  assert to_json([1, 2, 3], List[int]) == [1, 2, 3]

  @datamodel
  class A:
    a: str

  assert from_json(List[A], [{'a': 'foo'}, {'a': 'bar'}]) == [A('foo'), A('bar')]
  assert to_json([A('foo'), A('bar')], List[A]) == [{'a': 'foo'}, {'a': 'bar'}]


def test_model_converter_flatten():
  @datamodel
  class A:
    a: str

  @datamodel
  class B:
    a: A = field(flatten=True)
    b: str

  assert from_json(B, {'a': 'foo', 'b': 'bar'}) == B(A('foo'), 'bar')
  #assert to_json(B(A('foo'), 'bar')) == {'a': 'foo', 'b': 'bar'}


def test_model_converter_flatten_wildcard():
  @datamodel
  class A:
    a: str

  @datamodel
  class C:
    a: int
    remainder: Dict[str, A] = field(flatten=True)

  assert from_json(C, {'a': 42, 'b': {'a': 'foo'}, 'c': {'a': 'bar'}}) == C(42, {'b': A('foo'), 'c': A('bar')})
  assert to_json(C(42, {'b': A('foo'), 'c': A('bar')})) == {'a': 42, 'b': {'a': 'foo'}, 'c': {'a': 'bar'}}


def test_model_converter_strict():
  @datamodel
  class A:
    a: str

  assert from_json(A, {'a': 'foo'}) == A('foo')
  assert from_json(A, {'a': 'foo', 'b': 'bar'}) == A('foo')
  with raises(ConversionValueError) as excinfo:
    from_json(A, {'a': 'foo', 'b': 'bar'}, field_metadata=FieldMetadata(strict=True))
  assert str(excinfo.value) == f"$: strict conversion of {type_repr(A)} does not permit additional keys {{'b'}}"
