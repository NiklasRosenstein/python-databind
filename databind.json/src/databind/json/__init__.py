""" The #databind.json package implements the capabilities to bind JSON payloads to objects and the reverse. """

from __future__ import annotations

import json
import typing as t

from nr.util.generic import T

if t.TYPE_CHECKING:
    from databind.core.mapper import ObjectMapper
    from databind.core.settings import Setting, Settings

__version__ = "3.0.0"

JsonType = t.Union[
    None,
    bool,
    int,
    float,
    str,
    t.Dict[str, t.Any],
    t.List[t.Any],
]


def get_object_mapper(settings: t.Optional[Settings] = None) -> ObjectMapper[t.Any, JsonType]:
    from databind.core.mapper import ObjectMapper

    from databind.json.module import JsonModule

    mapper = ObjectMapper[t.Any, JsonType](settings)
    mapper.module.register(JsonModule())
    return mapper


@t.overload
def load(
    value: t.Any,
    type_: t.Type[T],
    filename: t.Optional[str] = None,
    settings: t.Optional[t.List[Setting]] = None,
) -> T:
    ...


@t.overload
def load(
    value: t.Any,
    type_: t.Any,
    filename: t.Optional[str] = None,
    settings: t.Optional[t.List[Setting]] = None,
) -> t.Any:
    ...


def load(
    value: t.Any,
    type_: t.Any,
    filename: t.Optional[str] = None,
    settings: t.Optional[t.List[Setting]] = None,
) -> t.Any:
    return get_object_mapper().deserialize(value, type_, filename, settings)


@t.overload
def loads(
    value: str,
    type_: t.Type[T],
    filename: t.Optional[str] = None,
    settings: t.Optional[t.List[Setting]] = None,
) -> T:
    ...


@t.overload
def loads(
    value: str,
    type_: t.Any,
    filename: t.Optional[str] = None,
    settings: t.Optional[t.List[Setting]] = None,
) -> t.Any:
    ...


def loads(
    value: str,
    type_: t.Any,
    filename: t.Optional[str] = None,
    settings: t.Optional[t.List[Setting]] = None,
) -> t.Any:
    return load(json.loads(value), type_, filename, settings)


def dump(
    value: t.Any,
    type_: t.Any,
    filename: t.Optional[str] = None,
    settings: t.Optional[t.List[Setting]] = None,
) -> JsonType:
    return get_object_mapper().serialize(value, type_, filename, settings)


def dumps(
    value: t.Any,
    type_: t.Any,
    filename: t.Optional[str] = None,
    settings: t.Optional[t.List[Setting]] = None,
    indent: t.Union[int, str, None] = None,
    sort_keys: bool = False,
) -> str:
    return json.dumps(dump(value, type_, filename, settings), indent=indent, sort_keys=sort_keys)
