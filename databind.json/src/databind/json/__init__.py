
""" The #databind.json package implements the capabilities to bind JSON payloads to objects and the reverse. """

from __future__ import annotations
import json
import typing as t

from nr.util.generic import T
from databind.core.context import Location
from databind.core.mapper import ObjectMapper
from databind.core.settings import Setting, Settings
from databind.json.module import JsonModule
from databind.json.direction import Direction

__version__ = '1.5.1'

JsonType = t.Union[
  None,
  bool,
  int,
  float,
  str,
  t.Dict[str, t.Any],
  t.List[t.Any],
]


class JsonMapper(ObjectMapper):

  def __init__(self, direction: Direction, settings: t.Optional[Settings] = None) -> None:
    super().__init__(settings)
    self.module.register(JsonModule(direction))

  @staticmethod
  def serializing(settings: t.Optional[Settings] = None) -> JsonMapper:
    """ Return a serializing JSON mapper. """

    return JsonMapper(Direction.SERIALIZE, settings)

  @staticmethod
  def deserializing(settings: t.Optional[Settings] = None) -> JsonMapper:
    """ Return a deserializing JSON mapper. """

    return JsonMapper(Direction.DESERIALIZE, settings)


serializer = JsonMapper.serializing()
deserializer = JsonMapper.deserializing()


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
) -> T: ...


def load(
  value: t.Any,
  type_: t.Any,
  filename: t.Optional[str] = None,
  settings: t.Optional[t.List[Setting]] = None,
) -> T:
  return deserializer.convert(value, type_, Location(filename, None, None), settings)


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
  return serializer.convert(value, type_, Location(filename, None, None), settings)


def dumps(
  value: t.Any,
  type_: t.Any,
  filename: t.Optional[str] = None,
  settings: t.Optional[t.List[Setting]] = None,
  indent: t.Union[int, str, None] = None,
  sort_keys: bool = False,
) -> str:
  return json.dumps(dump(value, type_, filename, settings), indent=indent, sort_keys=sort_keys)
