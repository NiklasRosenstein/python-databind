
from dataclasses import dataclass
from . import Annotation


@dataclass
class typeinfo(Annotation):
  # @:change-id !databind.core.typeinfo
  """
  Annotation for classes to override information about the type.
  """

  name: str
