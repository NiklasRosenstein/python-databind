
__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.12.0'

import datetime
import decimal
from nr.parsing.date import duration
from databind.core.objectmapper import SimpleModule
from databind.core.types import ListType, MapType, ObjectType, OptionalType, SetType, UnionType
from .modules.optional import OptionalConverter
from .modules.collection import CollectionConverter
from .modules.datetime import DatetimeJsonConverter, DurationConverter
from .modules.decimal import DecimalJsonConverter
from .modules.map import MapConverter
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

    self.add_converter_for_type(ObjectType, ObjectTypeConverter())
    self.add_converter_for_type(UnionType, UnionConverter())
    self.add_converter_for_type(bool, PlainJsonConverter())
    self.add_converter_for_type(float, PlainJsonConverter())
    self.add_converter_for_type(int, PlainJsonConverter())
    self.add_converter_for_type(str, PlainJsonConverter())
    self.add_converter_for_type(decimal.Decimal, DecimalJsonConverter())
    self.add_converter_for_type(datetime.date, DatetimeJsonConverter())
    self.add_converter_for_type(datetime.time, DatetimeJsonConverter())
    self.add_converter_for_type(datetime.datetime, DatetimeJsonConverter())
    self.add_converter_for_type(duration, DurationConverter())
    self.add_converter_for_type(OptionalType, OptionalConverter())
    self.add_converter_for_type(MapType, MapConverter())
    self.add_converter_for_type(ListType, CollectionConverter())
    self.add_converter_for_type(SetType, CollectionConverter())
