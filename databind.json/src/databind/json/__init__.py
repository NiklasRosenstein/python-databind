
__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '1.1.3'

import datetime
import decimal
import io
import json
import typing as t

from nr.parsing.date import duration

from databind.core import ObjectMapper, SimpleModule, ImplicitUnionType, ListType, MapType, ObjectType, OptionalType, SetType, UnionType
from .modules.any import AnyConverter
from .modules.collection import CollectionConverter
from .modules.datetime import DatetimeJsonConverter, DurationConverter
from .modules.decimal import DecimalJsonConverter
from .modules.enum import EnumConverter
from .modules.implicitunion import ImplicitUnionConverter
from .modules.map import MapConverter
from .modules.object import ObjectTypeConverter
from .modules.optional import OptionalConverter
from .modules.plain import PlainJsonConverter
from .modules.union import UnionConverter

__all__ = [
  'JsonModule',
  'JsonType',
  'mapper',
  'load',
  'loads',
  'dump',
  'dumps',
]

T = t.TypeVar('T')
JsonType = t.Union[t.Mapping, t.Collection, str, int, float, bool, None]


class JsonModule(SimpleModule):
  """
  A composite of all modules for JSON de/serialization.
  """

  def __init__(self, name: str = None) -> None:
    super().__init__(name)

    self.add_converter_for_type(object, AnyConverter())
    self.add_converter_for_type(ObjectType, ObjectTypeConverter())
    self.add_converter_for_type(UnionType, UnionConverter())
    self.add_converter_for_type(bool, PlainJsonConverter())
    self.add_converter_for_type(float, PlainJsonConverter())
    self.add_converter_for_type(int, PlainJsonConverter())
    self.add_converter_for_type(bytes, PlainJsonConverter())
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
    self.add_converter_for_type(ImplicitUnionType, ImplicitUnionConverter())
    self.add_converter_provider(EnumConverter())


def mapper() -> ObjectMapper:
  return ObjectMapper(JsonModule(), name=__name__)


new_mapper = mapper  # backwards compatibility <=1.0.1


def load(
  data: t.Union[JsonType, t.TextIO],
  type_: t.Type[T],
  mapper: ObjectMapper = None,
  filename: str = None,
  annotations: t.List[t.Any] = None,
  options: t.List[t.Any] = None,
) -> T:

  if hasattr(data, 'read'):
    if not filename:
      filename = getattr(data, 'name', None)
    data = json.load(t.cast(t.TextIO, data))
  return (mapper or new_mapper()).deserialize(data, type_, filename=filename, annotations=annotations, settings=options)


def loads(
  data: str,
  type_: t.Type[T],
  mapper: ObjectMapper = None,
  filename: str = None,
  annotations: t.List[t.Any] = None,
  options: t.List[t.Any] = None,
) -> T:
  return load(io.StringIO(data), type_, mapper, filename, annotations, options)


def dump(
  value: T,
  type_: t.Type[T] = None,
  mapper: ObjectMapper = None,
  annotations: t.List[t.Any] = None,
  options: t.List[t.Any] = None,
  out: t.TextIO = None,
) -> JsonType:

  data = (mapper or new_mapper()).serialize(value, type_ or type(value), annotations=annotations, settings=options)
  if out is not None:
    json.dump(data, out)
  return data


def dumps(
  value: T,
  type_: t.Type[T] = None,
  mapper: ObjectMapper = None,
  annotations: t.List[t.Any] = None,
  options: t.List[t.Any] = None,
) -> str:
  return json.dumps(dump(value, type_, mapper, annotations, options))
