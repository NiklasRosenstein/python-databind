
__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.1.1'

from typing import Optional, Type, TypeVar
from databind import json as _json
from databind.core import FieldMetadata, Registry, TypeHint

from .loader import loads, ParseError
from .dumper import dumps

T = TypeVar('T')

registry = Registry(None)
_json.register_json_converters(registry, strict=False)


def from_str(
  type_: Type[T],
  value: str,
  field_metadata: Optional[FieldMetadata] = None,
  registry: Optional[Registry] = None,
) -> T:
  return _json.from_json(type_, loads(value), field_metadata, registry or globals()['registry'])


def to_str(
  value: T,
  type_: Optional[Type[T]] = None,
  field_metadata: Optional[FieldMetadata] = None,
  registry: Optional[Registry] = None,
) -> str:
  return dumps(_json.to_json(value, type_, field_metadata, registry or globals()['registry']))
