
__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.1.3'

from typing import Any, Dict, Optional, TextIO, Type, TypeVar, Union
from databind import json as _json
from databind.core import FieldMetadata, Registry
import yaml

T = TypeVar('T')


def from_str(
  type_: Type[T],
  value: str,
  field_metadata: FieldMetadata = None,
  registry: Registry = None,
  Loader: Type[yaml.composer.Composer] = yaml.SafeLoader,
) -> T:
  return _json.from_json(type_, yaml.load(value, Loader=Loader), field_metadata, registry)


def from_stream(
  type_: Type[T],
  stream: TextIO,
  field_metadata: FieldMetadata = None,
  registry: Registry = None,
  Loader: Type[yaml.composer.Composer] = yaml.SafeLoader,
) -> T:
  return _json.from_json(type_, yaml.load(stream, Loader=Loader), field_metadata, registry)


def to_str(
  value: T,
  type_: Type[T]=None,
  field_metadata: FieldMetadata = None,
  registry: Registry=None,
  Dumper: Type[yaml.serializer.Serializer] = yaml.SafeDumper,
  options: Optional[Dict[str, Any]] = None,
) -> str:
  options = options or {}
  return yaml.dump(_json.to_json(value, type_, field_metadata, registry), Dumper=Dumper, **options)


def to_stream(
  stream: TextIO,
  value: T,
  type_: Type[T]=None,
  field_metadata: FieldMetadata = None,
  registry: Registry=None,
  Dumper: Type[yaml.serializer.Serializer] = yaml.SafeDumper,
  options: Optional[Dict[str, Any]] = None,
) -> None:
  options = options or {}
  yaml.dump(_json.to_json(value, type_, field_metadata, registry), stream, Dumper=Dumper, **options)
