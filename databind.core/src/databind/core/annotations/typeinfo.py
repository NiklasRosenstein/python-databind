
import typing as t
from dataclasses import dataclass
from . import Annotation, get_annotation


@dataclass
class typeinfo(Annotation):
  # @:change-id !databind.core.typeinfo
  """
  Annotation for classes to override information about the type.
  """

  name: str

  @staticmethod
  def get_name(type: t.Type) -> str:
    info = get_annotation(type, typeinfo, None)
    return info.name if info else type.__name__
