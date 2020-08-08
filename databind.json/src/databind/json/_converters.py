
import datetime
import decimal
import enum
from collections.abc import Mapping, Sequence
from typing import Any, Dict, List, Optional, T, Type, Union

from databind.core import (
  datamodel,
  enumerate_fields,
  is_datamodel,
  Context,
  ConversionTypeError,
  Converter,
  FieldMetadata,
  ModelMetadata,
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


class MixtypeConverter(Converter):
  """
  Handles the conversion of #Optional and #Union type hints. The `Optional[T]` type hint is
  just an alias for `Union[T, None]`, that's why this class needs to handle both cases.

  For multiple types defined in the #Union type hint, a conversion will be attempted in order
  of the types defined in the hint. If a conversion fails with a #ConversionTypeError, the
  next type is tried.
  """

  def _do_conversion(self, value, context, method):
    args = context.type.__args__
    if type(None) in args and value is None:
      return None
    for type_ in args:
      if type_ == type(None): continue
      try:
        return getattr(context.fork(type_, value), method)()
      except ConversionTypeError:
        pass
    raise context.type_error(f'expected {type_repr(context.type)}, got {type_repr(type(value))}')

  def from_python(self, value: Any, context: Context) -> Any:
    return self._do_conversion(value, context, 'from_python')

  def to_python(self, value: Any, context: Context) -> Any:
    return self._do_conversion(value, context, 'to_python')


class ObjectConverter(Converter):

  def _get_python_type(self, context: Context) -> Type:
    # TODO(NiklasRosenstein): Field-level option
    return context.registry.get_option(Dict, 'py_type', dict)

  def _do_conversion(self, value: Mapping, context: Context, method: str) -> Mapping:
    if not isinstance(value, Mapping):
      raise context.type_error(f'expected object, got {type_repr(type(value))}')
    key_type, value_type = context.type.__args__
    result = self._get_python_type(context)()
    for key, value in value.items():
      if key_type is not None:
        key = getattr(context.child(key, key_type, key), method)()
      if value_type is not None:
        value = getattr(context.child(key, value_type, value), method)()
      result[key] = value
    return result

  def from_python(self, value: Mapping, context: Context) -> Mapping:
    return self._do_conversion(value, context, 'from_python')

  def to_python(self, value: Mapping, context: Context) -> Mapping:
    return self._do_conversion(value, context, 'to_python')


class ModelConverter(Converter):
  """
  Handles the conversion of data models to and from JSON structures.
  """

  @datamodel
  class _FieldConversionData:
    name: str
    type: Type
    metadata: FieldMetadata
    target: List[str]

    @property
    def immediate_target(self) -> str:
      return self.target[-1]

  @datamodel
  class _ModelConversionData:
    metadata: ModelMetadata
    fields: List['_FieldConversionData']
    targets: List['_FieldConversionData']
    wildcard: Optional['_FieldConversionData']

  def _get_conversion_data(self, type_: Type) -> _ModelConversionData:
    fields = []
    targets = []
    wildcard = None
    for field in enumerate_fields(type_):
      if field.metadata.flatten and is_datamodel(field.type):
        for field_data in self._get_conversion_data(field.type).fields:
          field_data.target.append(field.name)
          fields.append(field_data)
        targets.append(self._FieldConversionData(field.name, field.type, field.metadata, ['*']))
      elif field.metadata.flatten:
        if not wildcard:
          wildcard = self._FieldConversionData(field.name, field.type, field.metadata, [])
      else:
        fields.append(self._FieldConversionData(field.name, field.type, field.metadata, ['*']))
    return self._ModelConversionData(ModelMetadata.for_type(type_), fields, targets, wildcard)

  def to_python(self, value, context: Context) -> dict:
    if not isinstance(value, Mapping):
      raise context.type_error(f'expected {type_repr(context.type)} (as mapping), got {type_repr(type(value))}')

    conversion_data = self._get_conversion_data(context.type)
    targets = {'*': {}}
    wildcard = None
    seen_keys = set()

    for field in conversion_data.fields:
      key = field.metadata.altname or field.name
      if key in value:
        targets.setdefault(field.immediate_target, {})[field.name] = context.child(
          field.name,
          field.type,
          value[key],
          field.metadata,
        ).to_python()
        seen_keys.add(key)

    if conversion_data.wildcard:
      field = conversion_data.wildcard
      wildcard = {k: v for k, v in value.items() if k not in seen_keys}
      wildcard = context.child(
        field.name,
        field.type,
        wildcard,
        field.metadata,
      ).to_python()
      targets['*'][field.name] = wildcard

    # Convert flattened fields.
    for field in conversion_data.targets:
      targets['*'][field.name] = context.child(
        field.name,
        field.type,
        targets.pop(field.name),
        field.metadata,
      ).to_python()

    # Strict conversion does not allow additional keys.
    if (conversion_data.metadata.strict or
        (context.field_metadata and context.field_metadata.strict) or
        context.registry.get_option(datamodel, 'strict', False)):
      additional_keys = set(value.keys()) - seen_keys
      if additional_keys:
        raise context.value_error(f'strict conversion of {type_repr(context.type)} does not permit additional keys {additional_keys}')

    assert len(targets) == 1
    return context.type(**targets['*'])

  def from_python(self, value, context: Context) -> Any:
    if not isinstance(value, context.type):
      raise context.type_error(f'expected {type_repr(context.type)}, got {type_repr(type(value))}')

    conversion_data = self._get_conversion_data(context.type)
    result = {}  # TODO(NiklasRosenstein): Option to override target conversion type.

    for field in enumerate_fields(context.type):
      field_value = context.child(
        field.name,
        field.type,
        getattr(value, field.name),
        field.metadata,
      ).from_python()
      if field.metadata.flatten:
        # Only update keys that don't already exist. This is to ensure consistency with
        # to_python() where we associate duplicate flattened fields only with the first
        # field that exposes it.
        result.update({k: v for k, v in field_value.items() if k not in result})
      else:
        result[field.metadata.altname or field.name] = field_value

    return result


class ArrayConverter(Converter):

  def _do_conversion(self, value, context, method):
    item_type = context.type.__args__[0]
    if not isinstance(value, Sequence):
      raise context.type_error(f'expected {type_repr(context.type)} (as sequence), got {type_repr(type(value))}')
    result = []  # TODO(NiklasRosenstein): Option to set conversion target type
    for index, item in enumerate(value):
      # Note: forwarding the FieldMetadata from the parent to the items.
      child_context = context.child(index, item_type, item, context.field_metadata)
      result.append(getattr(child_context, method)())
    return result

  def from_python(self, value, context):
    return self._do_conversion(value, context, 'from_python')

  def to_python(self, value, context):
    return self._do_conversion(value, context, 'to_python')


def register_json_converters(registry: Registry) -> None:
  registry.register_converter(int, IntConverter())
  registry.register_converter(str, StringConverter())
  registry.register_converter(float, FloatConverter())
  registry.register_converter(List, ArrayConverter())
  registry.register_converter(Dict, ObjectConverter())
  registry.register_converter(decimal.Decimal, DecimalConverter())
  registry.register_converter(enum.Enum, EnumConverter())
  #registry.register_converter(datetime.date, DateConverter())
  #registry.register_converter(datetime.datetime, DatetimeConverter())
  #registry.register_converter(datetime.timedelta, TimedeltaConverter())
  registry.register_converter(datamodel, ModelConverter())
  #registry.register_converter(uniontype, UnionConverter())
  registry.register_converter(Union, MixtypeConverter())
