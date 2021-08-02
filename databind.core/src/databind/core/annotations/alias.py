
import typing as t
from dataclasses import dataclass
from databind.core.annotations.base import Annotation


@dataclass
class alias(Annotation):
  # @:change-id !databind.core.alias
  """
  Used to specify one more alternative names of a field that shall be used during de-/serialization.
  If a field is aliased with this decoration, it's original field name will be ignored.

  While it is possible to use this annotation to decorate a class and this change the alias of all
  uses of the class as a field, it is usually used on a field descriptor to specify the alias only
  for that particular field.
  """

  aliases: t.Tuple[str, ...]

  def __init__(self, alias: str, *additional_aliases: str) -> None:
    self.aliases = (alias,) + additional_aliases

  def __repr__(self) -> str:
    return f'alias({", ".join(map(repr, self.aliases))})'
