
from __future__ import annotations

from databind.core.module import Module
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
    from databind.json.converters import AnyConverter, CollectionConverter, DatetimeConverter, DecimalConverter, \
        DurationConverter, EnumConverter, MappingConverter, OptionalConverter, PlainDatatypeConverter, \
        StringifyConverter

    self.register(AnyConverter())
    self.register(CollectionConverter(direction))
    self.register(DatetimeConverter(direction))
    self.register(DecimalConverter(direction))
    self.register(DurationConverter(direction))
    self.register(EnumConverter(direction))
    self.register(MappingConverter())
    self.register(OptionalConverter())
    self.register(PlainDatatypeConverter(direction))
    self.register(StringifyConverter(direction, uuid.UUID, lambda _, v: uuid.UUID(v)))
    self.register(StringifyConverter(direction, pathlib.PurePath, lambda t, v: t(v)))

    # self.register(UnionConverter(direction))
    # self.register(DataclassConverter(direction))

  @staticmethod
  def serializing() -> JsonModule:
    """ Return a serializing JSON module. """

    return JsonModule(Direction.SERIALIZE)

  @staticmethod
  def deserializing() -> JsonModule:
    """ Return a deserializing JSON module. """

    return JsonModule(Direction.DESERIALIZE)
