
""" The #databind.json package implements the capabilities to bind JSON payloads to objects and the reverse. """

from __future__ import annotations
import json
import typing as t

from nr.util.generic import T

if t.TYPE_CHECKING:
  from databind.core.mapper import BiObjectMapper
  from databind.core.settings import Setting, Settings

__version__ = '2.0.0a1'

JsonType = t.Union[
  None,
  bool,
  int,
  float,
  str,
  t.Dict[str, t.Any],
  t.List[t.Any],
]


def get_bimapper(settings: t.Optional[Settings] = None) -> BiObjectMapper[JsonType]:
  from databind.core.mapper import BiObjectMapper, ObjectMapper
  from databind.json.module import JsonModule
  serializer = ObjectMapper(settings)
  serializer.module.register(JsonModule.serializing())
  deserializer = ObjectMapper(settings)
  deserializer.module.register(JsonModule.deserializing())
  return BiObjectMapper(serializer, deserializer)


@t.overload
def load(
  value: t.Any,
  type_: t.Type[T],
  filename: t.Optional[str] = None,
  settings: t.Optional[t.List[Setting]] = None,
) -> T: ...


@t.overload
def load(
  value: t.Any,
  type_: t.Any,
  filename: t.Optional[str] = None,
  settings: t.Optional[t.List[Setting]] = None,
) -> t.Any: ...


def load(
  value: t.Any,
  type_: t.Any,
  filename: t.Optional[str] = None,
  settings: t.Optional[t.List[Setting]] = None,
) -> t.Any:
  return get_bimapper().deserialize(value, type_, filename, settings)


@t.overload
def loads(
  value: str,
  type_: t.Type[T],
  filename: t.Optional[str] = None,
  settings: t.Optional[t.List[Setting]] = None,
) -> T: ...


@t.overload
def loads(
  value: str,
  type_: t.Any,
  filename: t.Optional[str] = None,
  settings: t.Optional[t.List[Setting]] = None,
) -> T: ...


def loads(
  value: str,
  type_: t.Any,
  filename: t.Optional[str] = None,
  settings: t.Optional[t.List[Setting]] = None,
) -> T:
  return load(json.loads(value), type_, filename, settings)


def dump(
  value: t.Any,
  type_: t.Any,
  filename: t.Optional[str] = None,
  settings: t.Optional[t.List[Setting]] = None,
) -> JsonType:
  return get_bimapper().serialize(value, type_, filename, settings)


def dumps(
  value: t.Any,
  type_: t.Any,
  filename: t.Optional[str] = None,
  settings: t.Optional[t.List[Setting]] = None,
  indent: t.Union[int, str, None] = None,
  sort_keys: bool = False,
) -> str:
  return json.dumps(dump(value, type_, filename, settings), indent=indent, sort_keys=sort_keys)
