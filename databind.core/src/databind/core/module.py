
from __future__ import annotations
import typing as t

if t.TYPE_CHECKING:
  from databind.core.converter import Converter


class Module:
  """ A module is a collection of #Converter#s. """

  def __init__(self, name: str) -> None:
    self.name = name
    self.converters: t.List[Converter] = []

  def __repr__(self) -> str:
    return f'Module({self.name!r})'

  def register(self, converter: Converter) -> None:
    from databind.core.converter import Converter
    assert isinstance(converter, Converter), converter
    self.converters.append(converter)
