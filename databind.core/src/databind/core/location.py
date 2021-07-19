
import typing as t
from dataclasses import dataclass
from .types import BaseType


def _get_location_chain(location: 'Location') -> t.List['Location']:
  chain: t.List[Location] = []
  current: t.Optional[Location] = location
  while current is not None:
    chain.append(current)
    current = current.parent
  chain.reverse()
  return chain


def _get_filename_and_pos_string(filename: t.Optional[str], pos: t.Optional['Position']) -> str:
  result = filename
  if pos is not None:
    result = f'{result}:{pos.line}:{pos.col}'
  return f'[{result}]'


class Position(t.NamedTuple):
  # @:change-id Location.Position

  line: int
  col: int


@dataclass
class Location:
  """
  Represents the location of a value in a nested structure, possibly spanning more than one input
  source (which can be discriminated using a "filename" property). A location may also be associated
  with type information that is used to render the string representation.
  """

  #: The parent of the location.
  parent: t.Optional['Location']

  #: The expected type of the value at this location.
  type: BaseType

  #: The key of the location. This is `None` if the location represents the root of the nested
  #: structure. Locations with a `None` key may still have a #parent in case of a location that
  #: represents a different source but was reached from another location.
  key: t.Union[str, int, None] = None

  #: The filename of the input source. If not set, the parent location's filename is considered
  #: this location's filename (although the value is not actively inherited when the #Location
  #: object is created).
  filename: t.Optional[str] = None

  #: The line and column of the location (optional).
  pos: t.Optional[Position] = None

  def __str__(self) -> str:
    """
    Converts the location to a string representation of the form

        [filename:line:col] ($ type) -> (key type) -> ...
    """

    parts: t.List[str] = []
    prev_filename: t.Optional[str] = None

    for loc in _get_location_chain(self):
      source_changed = bool(not prev_filename or loc.filename and loc.filename != prev_filename)
      if source_changed:
        parts.append(_get_filename_and_pos_string(loc.filename, loc.pos))
        parts.append(' ')

      name = '$' if loc.key is None else f'.{loc.key}'
      parts.append(f'({name} {loc.type})')
      parts.append(' -> ')

      if loc.filename:
        prev_filename = loc.filename

    parts.pop()  # Remove the last '->'
    return ''.join(parts)

  def push(self,
    type_: BaseType,
    key: t.Union[str, int, None],
    filename: t.Optional[str],
    pos: t.Optional[Position]
  ) -> 'Location':
    return Location(self, type_, key, filename, pos)
