
import decimal
import enum
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
