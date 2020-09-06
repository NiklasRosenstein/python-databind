
__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.4.1'

import json
from typing import Optional, Type, TypeVar, Union
from databind.core import Context, FieldMetadata, Registry
from ._converters import register_json_converters

__all__ = [
  'register_json_converters',
  'registry',
  'from_json',
  'to_json',
  'from_str',
  'to_str',
]

T = TypeVar('T')
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


def to_str(
  value: T,
  type_: Type[T]=None,
  field_metadata: FieldMetadata = None,
  registry: Registry=None,
) -> str:
  return json.dumps(to_json(value, type_, field_metadata, registry))
