
import dataclasses
import typing as t
import typing_extensions as te

import typeapi
from databind.core.settings import Flattened, Required
from databind.core.schema import Field, Schema, convert_dataclass_to_schema, convert_to_schema, \
    convert_typed_dict_to_schema, get_fields_expanded
from nr.util.generic import T, U


def test_convert_to_schema():
  # Test dataclass detection
  @dataclasses.dataclass
  class A:
    a: int
    b: str
  assert convert_to_schema(typeapi.of(A)) == Schema({
    'a': Field(typeapi.of(int)),
    'b': Field(typeapi.of(str)),
  }, A)
  assert convert_to_schema(typeapi.of(te.Annotated[A, 42])) == Schema({
    'a': Field(typeapi.of(int)),
    'b': Field(typeapi.of(str)),
  }, A, [42])

  # Test typed dict detection
  class Movie(te.TypedDict):
    name: str
    year: int
  assert convert_to_schema(typeapi.of(Movie)) == Schema({
    'name': Field(typeapi.of(str)),
    'year': Field(typeapi.of(int)),
  }, Movie)


def test_get_fields_expanded():
  class Dict1(te.TypedDict):
    a: int
    b: str

  @dataclasses.dataclass
  class Class2:
    a: te.Annotated[Dict1, Flattened()]  # The field "a" can be shadowed by a field of its own members
    c: int

  class Dict3(te.TypedDict):
    d: te.Annotated[Class2, Flattened()]

  @dataclasses.dataclass
  class Class4:
    f: te.Annotated[Dict3, Flattened()]

  schema = convert_to_schema(typeapi.of(Dict1))
  assert get_fields_expanded(schema) == {}

  schema = convert_to_schema(typeapi.of(Class2))
  assert get_fields_expanded(schema) == {
    'a': {
      'a': Field(typeapi.of(int)),
      'b': Field(typeapi.of(str)),
    }
  }

  schema = convert_to_schema(typeapi.of(Dict3))
  assert get_fields_expanded(schema) == {
    'd': {
      'a': Field(typeapi.of(int)),
      'b': Field(typeapi.of(str)),
      'c': Field(typeapi.of(int)),
    }
  }

  schema = convert_to_schema(typeapi.of(Class4))
  assert get_fields_expanded(schema) == {
    'f': {
      'a': Field(typeapi.of(int)),
      'b': Field(typeapi.of(str)),
      'c': Field(typeapi.of(int)),
    }
  }


def test_convert_dataclass_to_schema_simple():
  @dataclasses.dataclass
  class A:
    a: int
    b: str
  assert convert_dataclass_to_schema(A) == Schema({
    'a': Field(typeapi.of(int)),
    'b': Field(typeapi.of(str)),
  }, A)


def test_convert_dataclass_to_schema_with_defaults():
  @dataclasses.dataclass
  class A:
    a: int = 42
    b: te.Annotated[int, Required()] = 42
    c: str = dataclasses.field(default_factory=str)
  assert convert_dataclass_to_schema(A) == Schema({
    'a': Field(typeapi.of(int), False, 42),
    'b': Field(typeapi.of(te.Annotated[int, Required()]), True, 42),
    'c': Field(typeapi.of(str), False, default_factory=str),
  }, A)


def test_convert_dataclass_to_schema_nested():
  @dataclasses.dataclass
  class A:
    a: int
  @dataclasses.dataclass
  class B:
    a: A
    b: str
  assert convert_dataclass_to_schema(B) == Schema({
    'a': Field(typeapi.of(A)),
    'b': Field(typeapi.of(str)),
  }, B)


def test_convert_dataclass_to_schema_inheritance():
  @dataclasses.dataclass
  class A:
    a: int
  @dataclasses.dataclass
  class B(A):
    b: str
  assert convert_dataclass_to_schema(B) == Schema({
    'a': Field(typeapi.of(int)),
    'b': Field(typeapi.of(str)),
  }, B)


def test_convert_dataclass_to_schema_generic():
  @dataclasses.dataclass
  class A(t.Generic[T]):
    a: T
  assert convert_dataclass_to_schema(A) == Schema({
    'a': Field(typeapi.of(T)),
  }, A)
  assert convert_dataclass_to_schema(A[int]) == Schema({
    'a': Field(typeapi.of(int)),
  }, A)


def test_convert_dataclass_overriden_field_type():
  @dataclasses.dataclass
  class A:
    a: int
  @dataclasses.dataclass
  class B(A):
    a: str
  assert convert_dataclass_to_schema(B) == Schema({
    'a': Field(typeapi.of(str))
  }, B)


def test_convert_dataclass_to_schema_type_var_without_generic():
  @dataclasses.dataclass
  class A:
    a: T  # type: ignore[valid-type]  # Type variable "nr.util.generic.T" is unbound
  @dataclasses.dataclass
  class B(A, t.Generic[T]):
    b: T
  assert convert_dataclass_to_schema(B) == Schema({
    'a': Field(typeapi.of(T)),
    'b': Field(typeapi.of(T)),
  }, B)
  assert convert_dataclass_to_schema(B[int]) == Schema({
    'a': Field(typeapi.of(T)),
    'b': Field(typeapi.of(int)),
  }, B)


def test_convert_dataclass_to_schema_generic_nested():
  @dataclasses.dataclass
  class A(t.Generic[T]):
    a: T
  @dataclasses.dataclass
  class B1:
    a: A[int]
    b: str
  @dataclasses.dataclass
  class B2(t.Generic[U]):
    a: A[U]
    b: str
  assert convert_dataclass_to_schema(B1) == Schema({
    'a': Field(typeapi.of(A[int])),
    'b': Field(typeapi.of(str)),
  }, B1)
  assert convert_dataclass_to_schema(B2) == Schema({
    'a': Field(typeapi.of(A[U])),
    'b': Field(typeapi.of(str)),
  }, B2)
  assert convert_dataclass_to_schema(B2[int]) == Schema({
    'a': Field(typeapi.of(A[int])),
    'b': Field(typeapi.of(str)),
  }, B2)


def test_convert_dataclass_to_schema_generic_inheritance():
  @dataclasses.dataclass
  class A(t.Generic[T]):
    a: T
  @dataclasses.dataclass
  class B1(A[int]):
    b: str
  assert convert_dataclass_to_schema(B1) == Schema({
    'a': Field(typeapi.of(int)),
    'b': Field(typeapi.of(str)),
  }, B1)

  @dataclasses.dataclass
  class B2(A[U], t.Generic[U]):
    b: str
  assert convert_dataclass_to_schema(B2) == Schema({
    'a': Field(typeapi.of(U)),
    'b': Field(typeapi.of(str)),
  }, B2)
  assert convert_dataclass_to_schema(B2[int]) == Schema({
    'a': Field(typeapi.of(int)),
    'b': Field(typeapi.of(str)),
  }, B2)


def test_convert_typed_dict_to_schema_total() -> None:
  class Movie(te.TypedDict):
    name: str
    year: int = 42  # type: ignore[misc]
  assert convert_typed_dict_to_schema(Movie) == Schema({
    'name': Field(typeapi.of(str)),
    'year': Field(typeapi.of(int), False, default=42),
  }, Movie)


def test_convert_typed_dict_to_schema_functional():
  Movie = te.TypedDict('Movie', {'name': str, 'year': int})
  Movie.year = 42
  assert convert_typed_dict_to_schema(Movie) == Schema({
    'name': Field(typeapi.of(str)),
    'year': Field(typeapi.of(int), False, default=42),
  }, Movie)


def test_convert_typed_dict_to_schema_not_total():
  class Movie(te.TypedDict, total=False):
    name: str
    year: int
  assert convert_typed_dict_to_schema(Movie) == Schema({
    'name': Field(typeapi.of(str), False),
    'year': Field(typeapi.of(int), False),
  }, Movie)