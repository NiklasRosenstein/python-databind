
__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.12.0'

import datetime
import decimal
from databind.core.api import Direction, IConverter
from databind.core.objectmapper import SimpleModule
from databind.core.types import BaseType, CollectionType, ObjectType, UnionType
from .modules.collection import CollectionConverter
from .modules.datetime import DatetimeJsonConverter
from .modules.decimal import DecimalJsonConverter
from .modules.object import ObjectTypeConverter
from .modules.plain import PlainJsonConverter
from .modules.union import UnionConverter

__all__ = [
  'JsonModule',
]


class JsonModule(SimpleModule):
  """
  A composite of all modules for JSON de/serialization.
  """

  def __init__(self, name: str = None) -> None:
    super().__init__(name)

    conv = PlainJsonConverter()
    for type_ in (bool, float, int, str):
      self.add_converter_for_type(type_, conv, Direction.deserialize)
      self.add_converter_for_type(type_, conv, Direction.serialize)

    conv = DecimalJsonConverter()
    self.add_converter_for_type(decimal.Decimal, conv, Direction.deserialize)
    self.add_converter_for_type(decimal.Decimal, conv, Direction.serialize)

    conv = DatetimeJsonConverter()
    for type_ in (datetime.date, datetime.datetime, datetime.time):
      self.add_converter_for_type(type_, conv, Direction.deserialize)
      self.add_converter_for_type(type_, conv, Direction.serialize)

  def get_converter(self, type_: BaseType, direction: Direction) -> IConverter:
    if isinstance(type_, CollectionType):
      return CollectionConverter()
    elif isinstance(type_, ObjectType):
      return ObjectTypeConverter()
    elif isinstance(type_, UnionType):
        return UnionConverter()
    return super().get_converter(type_, direction)
