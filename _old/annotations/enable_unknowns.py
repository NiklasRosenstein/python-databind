
import dataclasses
import typing as t

from databind.core.mapper.location import Location

if t.TYPE_CHECKING:
  from databind.core.mapper.converter import Context


@dataclasses.dataclass
class enable_unknowns:
  """
  This annotation is not supposed to be used to decorate a field or class, but instead can be
  given globally as an option to #ObjectMapper to allow unknown fields when deserializing
  #ObjectType's, as well as optionally receiving callbacks as unknown fields are encountered.
  """

  #: A callback to be invoked when a set of unknown keys are encountered.
  callback: t.Optional[t.Callable[['Context', t.Set[str]], None]] = None


class collect_unknowns:
  """
  Collect unknown keys into this object.
  """

  class Entry(t.NamedTuple):
    location: Location
    keys: t.Set[str]

  entries: t.List[Entry]

  def __init__(self) -> None:
    self.entries = []

  def __bool__(self) -> bool:
    return bool(self.entries)

  def __iter__(self) -> t.Iterator[Entry]:
    return iter(self.entries)

  def callback(self, ctx: 'Context', keys: t.Set[str]) -> None:
    self.entries.append(collect_unknowns.Entry(ctx.location, keys))

  def __call__(self) -> enable_unknowns:
    return enable_unknowns(self.callback)
