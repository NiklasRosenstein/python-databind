
import datetime
import decimal
import enum
from typing import Any, Optional

from databind.core import (
  datamodel,
  Context,
  Converter,
  Registry,
  type_repr,
  uniontype,
)
from databind.core.utils import find


class IntConverter(Converter):

  def from_python(self, value: Any, context: Context) -> int:
    if hasattr(value, '__index__'):
      return value.__index__()
    if isinstance(value, int):
      return value
    raise context.type_error(f'expected integer, got {type_repr(type(value))}')

  to_python = from_python


class StringConverter(Converter):

  def from_python(self, value: Any, context: Context) -> str:
    if isinstance(value, str):
      return value
    raise context.type_error(f'expected str, got {type_repr(type(value))}')

  to_python = from_python


class FloatConverter(Converter):

  def from_python(self, value: Any, context: Context) -> float:
    if isinstance(value, (float, int)):
      return float(value)
    raise context.type_error(f'expected float, got {type_repr(type(value))}')

  to_python = from_python


class DecimalConverter(Converter):
  """
  Converts between #decimal.Decimal and strings. The first #decimal.Context in the field
  formats will be used as the decimal context, or the "context" option in the registry
  associated with the #decimal.Decimal type.

  Decimal values are automatically cast into the specified context. This means that converting
  a decimal string with a higher precision than defined into Python will truncate it's precision.
  """

  def _get_decimal_context(self, context: Context) -> decimal.Context:
    dec_context = find(lambda x: isinstance(x, decimal.Context),
                       (context.field_metadata and context.field_metadata.formats) or [])
    dec_context = dec_context or context.registry.get_option(decimal.Decimal, 'context')
    return dec_context or decimal.getcontext()

  def from_python(self, value: decimal.Decimal, context: Context) -> str:
    if not isinstance(value, decimal.Decimal):
      raise context.type_error(f'expected decimal.Decimal, got {type_repr(type(value))}')
    context = self._get_decimal_context(context)
    return str(context.create_decimal(value))

  def to_python(self, value: str, context: Context) -> str:
    if not isinstance(value, str):
      raise context.type_error(f'expected decimal (as string), from {type_repr(type(value))}')
    try:
      return self._get_decimal_context(context).create_decimal(value)
    except ValueError as exc:
      raise context.value_error(str(exc))


class EnumConverter(Converter):
  """
  Converts Python enums to and from strings.
  """

  def from_python(self, value: enum.Enum, context: Context) -> str:
    if not isinstance(value, context.type):
      raise context.type_error(f'expected {type_repr(context.type)}, got {type_repr(type(value))}')
    return value.name

  def to_python(self, value: str, context: Context) -> enum.Enum:
    if not isinstance(value, str):
      raise context.type_error(f'expected {type_repr(context.type)} (as string), got {type_repr(type(value))}')
    try:
      return context.type[value]
    except KeyError:
      raise context.value_error(f'invalid value for enum {type_repr(context.type)}: {value!r}')


def register_json_converters(registry: Registry) -> None:
  registry.register_converter(int, IntConverter())
  registry.register_converter(str, StringConverter())
  registry.register_converter(float, FloatConverter())
  registry.register_converter(decimal.Decimal, DecimalConverter())
  registry.register_converter(enum.Enum, EnumConverter())
  #registry.register_converter(datetime.date, DateConverter())
  #registry.register_converter(datetime.datetime, DatetimeConverter())
  #registry.register_converter(datetime.timedelta, TimedeltaConverter())
  #registry.register_converter(datamodel, ModelConverter())
  #registry.register_converter(uniontype, UnionConverter())
  #registry.register_converter(Optional, OptionalConverter())
  #registry.register_converter(Union, MixtypeConverter())
