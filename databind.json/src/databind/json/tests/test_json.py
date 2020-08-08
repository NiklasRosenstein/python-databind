
import datetime
import decimal
import enum
from typing import Dict, List, Optional, Union
from databind.core import *
from databind.json import *
from nr.parsing.date import Duration, Iso8601
from pytest import raises


def test_bool_converter():
  assert from_json(bool, True) == True
  assert to_json(False) == False
  with raises(ConversionTypeError) as excinfo:
    from_json(bool, "foo")
  assert str(excinfo.value) == '$: expected bool, got str'


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


def test_datetime_converter():
  assert from_json(datetime.datetime, '2020-01-04T14:23:00.0Z') == Iso8601().parse('2020-01-04T14:23:00.0Z')

  now = datetime.datetime.now()
  assert to_json(now) == Iso8601().format(now)


def test_date_converter():
  assert from_json(datetime.date, '2020-06-01') == datetime.date(2020, 6, 1)
  assert to_json(datetime.date(2020, 6, 1)) == '2020-06-01'


def test_duration_converter():
  assert from_json(Duration, 'PT4H') == Duration(hours=4)
  assert to_json(Duration(years=20, hours=3, seconds=15)) == 'P20YT3H15S'


def test_uniontype_converter():
  @uniontype(type_key='T', flat=False)
  class A:
    int: Optional[int]
    str: str

  assert from_json(A, {'T': 'int', 'int': 42}) == 42
  assert from_json(A, {'T': 'int', 'int': None}) == None
  assert from_json(A, {'T': 'str', 'str': "foo"}) == "foo"
  with raises(ConversionTypeError) as excinfo:
    from_json(A, {'T': 'str', 'str': None})
  assert str(excinfo.value) == "$.str: expected str, got NoneType"

  assert to_json(42, A) == {'T': 'int', 'int': 42}
  assert to_json("bar", A) == {'T': 'str', 'str': "bar"}


  @uniontype(type_key='T', flat=False, container=True)
  class A:
    int: Optional[int]
    str: str

  assert from_json(A, {'T': 'int', 'int': 42}) == A('int', 42)
  assert from_json(A, {'T': 'int', 'int': 42}) != A('int', 43)
  assert from_json(A, {'T': 'int', 'int': 42}) != A('str', "foo")
  assert from_json(A, {'T': 'int', 'int': None}) == A('int', None)
  assert from_json(A, {'T': 'str', 'str': "foo"}) == A('str', "foo")
  with raises(ConversionTypeError) as excinfo:
    from_json(A, {'T': 'str', 'str': None})
  assert str(excinfo.value) == "$.str: expected str, got NoneType"

  assert to_json(A('int', 42)) == {'T': 'int', 'int': 42}
  assert to_json(A('int', None)) == {'T': 'int', 'int': None}
  assert to_json(A('str', "foo")) == {'T': 'str', 'str': "foo"}


def test_uniontype_converter_with_models():
  @datamodel
  class A:
    field_a: int

  @datamodel
  class B:
    field_b: str

  @uniontype
  class C:
    a: A
    b: B

  assert from_json(C, {'type': 'a', 'field_a': 42}) == A(42)
  assert from_json(C, {'type': 'b', 'field_b': "foo"}) == B("foo")
  assert to_json(A(42), C) == {'type': 'a', 'field_a': 42}
  assert to_json(B("foo"), C) == {'type': 'b', 'field_b': "foo"}
