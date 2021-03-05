
__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.11.0'

import json
from typing import Optional, TextIO, Type, TypeVar, Union
from databind.core import Context, FieldMetadata, Registry
from ._converters import register_json_converters

__all__ = [
  'register_json_converters',
  'registry',
  'from_json',
  'from_str',
  'from_stream',
  'to_json',
  'to_str',
  'to_stream',
  'cast',
]

T = TypeVar('T')
R = TypeVar('R')
JsonType = Union[dict, list, str, int, float]

registry = Registry(None)
register_json_converters(registry)


def _registry(reg: Registry = None) -> Registry:
  return reg or registry


def from_json(
  type_: Type[T],
  value: JsonType,
  field_metadata: FieldMetadata = None,
  registry: Registry = None,
) -> T:
  return _registry(registry).make_context(type_ or type(value), value, field_metadata).to_python()


def to_json(
  value: T,
  type_: Type[T]=None,
  field_metadata: FieldMetadata = None,
  registry: Registry = None,
) -> JsonType:
  return _registry(registry).make_context(type_ or type(value), value, field_metadata).from_python()


def from_str(
  type_: Type[T],
  value: str,
  field_metadata: FieldMetadata = None,
  registry: Registry = None,
) -> T:
  return from_json(type_, json.loads(value), field_metadata, registry)


def from_stream(
  type_: Type[T],
  stream: TextIO,
  field_metadata: FieldMetadata = None,
  registry: Registry = None,
) -> T:
  return from_json(type_, json.load(stream), field_metadata, registry)


def to_str(
  value: T,
  type_: Type[T]=None,
  field_metadata: FieldMetadata = None,
  registry: Registry=None,
) -> str:
  return json.dumps(to_json(value, type_, field_metadata, registry))


def to_stream(
  stream: TextIO,
  value: T,
  type_: Type[T]=None,
  field_metadata: FieldMetadata = None,
  registry: Registry=None,
) -> None:
  json.dump(to_json(value, type_, field_metadata, registry), stream)


def cast(
  target_type: Type[R],
  value: T,
  type_: Optional[Type[T]] = None,
  registry: Registry = None,
) -> R:
  return from_json(target_type, to_json(value, type_, registry=registry), registry=registry)
