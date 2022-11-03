from __future__ import annotations

from typing import Iterator

from databind.core.context import Context
from databind.core.converter import Converter, Module

from databind.json.direction import Direction
from databind.json.settings import JsonConverter


class JsonModule(Module):
    """The JSON module combines all converters provided by the #databind.json package in one usable module. The
    direction in which the converters should convert must be specified with the *direction* argument. Alternatively,
    use one of the convenience static methods #serializing() and #deserializing()."""

    def __init__(self, direction: Direction) -> None:
        super().__init__(f"JSON ({direction.name.lower()}")
        self.direction = direction

        import pathlib
        import uuid

        from nr.util.date import duration

        from databind.json.converters import (
            AnyConverter,
            CollectionConverter,
            DatetimeConverter,
            DecimalConverter,
            EnumConverter,
            LiteralConverter,
            MappingConverter,
            OptionalConverter,
            PlainDatatypeConverter,
            SchemaConverter,
            StringifyConverter,
            UnionConverter,
        )

        self.register(AnyConverter())
        self.register(CollectionConverter(direction))
        self.register(DatetimeConverter(direction))
        self.register(DecimalConverter(direction))
        self.register(EnumConverter(direction))
        self.register(MappingConverter(direction))
        self.register(OptionalConverter())
        self.register(PlainDatatypeConverter(direction))
        self.register(UnionConverter(direction))
        self.register(SchemaConverter(direction))
        self.register(StringifyConverter(direction, uuid.UUID))
        self.register(StringifyConverter(direction, pathlib.Path))
        self.register(StringifyConverter(direction, pathlib.PurePath))
        self.register(StringifyConverter(direction, duration, duration.parse))
        self.register(LiteralConverter())

    def get_converters(self, ctx: Context) -> Iterator[Converter]:
        converter_setting = ctx.get_setting(JsonConverter)
        if converter_setting is not None:
            yield converter_setting.factory(self.direction)
        yield from super().get_converters(ctx)

    @staticmethod
    def serializing() -> JsonModule:
        """Return a serializing JSON module."""

        return JsonModule(Direction.SERIALIZE)

    @staticmethod
    def deserializing() -> JsonModule:
        """Return a deserializing JSON module."""

        return JsonModule(Direction.DESERIALIZE)
