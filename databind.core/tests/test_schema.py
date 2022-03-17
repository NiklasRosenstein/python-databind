
import dataclasses
import typing as t
import typing_extensions as te

import typeapi
from databind.core.settings import Required
from databind.core.schema import Field, Schema, convert_dataclass_to_schema
from nr.util.generic import T, U


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
  @dataclasses.dataclass
  class B2(A[U], t.Generic[U]):
    b: str
  assert convert_dataclass_to_schema(B1) == Schema({
    'a': Field(typeapi.of(int)),
    'b': Field(typeapi.of(str)),
  }, B1)
  assert convert_dataclass_to_schema(B2) == Schema({
    'a': Field(typeapi.of(U)),
    'b': Field(typeapi.of(str)),
  }, B2)
  assert convert_dataclass_to_schema(B2[int]) == Schema({
    'a': Field(typeapi.of(int)),
    'b': Field(typeapi.of(str)),
  }, B2)
