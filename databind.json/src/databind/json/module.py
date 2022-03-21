
from __future__ import annotations

from databind.core.converter import Module
from databind.json.direction import Direction


class JsonModule(Module):
  """ The JSON module combines all converters provided by the #databind.json package in one usable module. The
  direction in which the converters should convert must be specified with the *direction* argument. Alternatively,
  use one of the convenience static methods #serializing() and #deserializing(). """

  def __init__(self, direction: Direction) -> None:
    super().__init__(f'JSON ({direction.name.lower()}')
    self.direction = direction

    import uuid
    import pathlib
    from nr.util.date import duration
    from databind.json.converters import AnyConverter, CollectionConverter, DatetimeConverter, DecimalConverter, \
        EnumConverter, MappingConverter, OptionalConverter, PlainDatatypeConverter, SchemaConverter, \
        StringifyConverter, UnionConverter

    self.register(AnyConverter())
    self.register(CollectionConverter(direction))
    self.register(DatetimeConverter(direction))
    self.register(DecimalConverter(direction))
    self.register(EnumConverter(direction))
    self.register(MappingConverter(direction))
    self.register(OptionalConverter())
    self.register(PlainDatatypeConverter(direction))
    self.register(SchemaConverter(direction))
    self.register(StringifyConverter(direction, uuid.UUID))
    self.register(StringifyConverter(direction, pathlib.Path))
    self.register(StringifyConverter(direction, pathlib.PurePath))
    self.register(StringifyConverter(direction, duration, duration.parse))
    self.register(UnionConverter(direction))

  @staticmethod
  def serializing() -> JsonModule:
    """ Return a serializing JSON module. """

    return JsonModule(Direction.SERIALIZE)

  @staticmethod
  def deserializing() -> JsonModule:
    """ Return a deserializing JSON module. """

    return JsonModule(Direction.DESERIALIZE)
