
import typing as t
from dataclasses import dataclass
from databind.core.annotations.base import Annotation, get_annotation


@dataclass
class typeinfo(Annotation):
  # @:change-id !databind.core.typeinfo
  """
  Annotation for classes to override information about the type.
  """

  name: t.Optional[str] = None

  deserialize_as: t.Optional[t.Type] = None

  @staticmethod
  def get_name(type: t.Type) -> str:
    info = get_annotation(type, typeinfo, None)
    return (info.name if info else None) or type.__name__

