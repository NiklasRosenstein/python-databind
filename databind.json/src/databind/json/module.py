
from __future__ import annotations

from databind.core.module import Module
from databind.json.direction import Direction


class JsonModule(Module):
  """ The JSON module combines all converters provided by the #databind.json package in one usable module. The
  direction in which the converters should convert must be specified with the *direction* argument. Alternatively,
  use one of the convenience static methods #serializing() and #deserializing(). """

  def __init__(self, direction: Direction) -> None:
    self.direction = direction

    from databind.json.converters import AnyConverter, PlainDatatypeConverter

    self.register(AnyConverter())
    self.register(PlainDatatypeConverter(direction))

  @staticmethod
  def serializing() -> JsonModule:
    """ Return a serializing JSON module. """

    return JsonModule(Direction.SERIALIZE)

  @staticmethod
  def deserializing() -> JsonModule:
    """ Return a deserializing JSON module. """

    return JsonModule(Direction.DESERIALIZE)
