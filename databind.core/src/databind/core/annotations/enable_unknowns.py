
import dataclasses
import typing as t

if t.TYPE_CHECKING:
  from databind.core.api import Context


@dataclasses.dataclass
class enable_unknowns:
  """
  This annotation is not supposed to be used to decorate a field or class, but instead can be
  given globally as an option to #ObjectMapper to allow unknown fields when deserializing
  #ObjectType's, as well as optionally receiving callbacks as unknown fields are encountered.
  """

  # A callback to be invoked when a set of unknown keys are encountered.
  callback: t.Optional[t.Callable[['Context', t.Set[str]], None]] = None
