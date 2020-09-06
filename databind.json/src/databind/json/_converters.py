
import abc
import datetime
import decimal
import enum
import logging
import traceback
import types
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypeVar, Type, Union

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
  UnionMetadata,
  UnionTypeError,
  TypeHint,
)
from databind.core.utils import find
from nr.parsing.date import create_datetime_format_set, DatetimeFormat, Duration, Iso8601  # type: ignore

T = TypeVar('T')
logger = logging.getLogger(__name__)


def _get_log_level(logger: logging.Logger) -> int:
  while logger.level == 0 and logger:
    logger = logger.parent
  if logger:
    return logger.level
  return 0


def _indent_exc(exc: Exception) -> str:
  lines = []
  for index, line in enumerate(str(exc).splitlines()):
    if index > 0:
      line = '| ' + line
    lines.append(line)
  return '\n'.join(lines)


class _PodConverter(Converter):

  def __init__(self, strict: bool = True) -> None:
    self.strict = strict


class BoolConverter(_PodConverter):

  def from_python(self, value, context):
    if not isinstance(value, context.type) and self.strict:
      raise context.type_error(f'expected {type_repr(context.type)}, got {type_repr(type(value))}')
    return bool(value)

  to_python = from_python


class IntConverter(_PodConverter):

  def from_python(self, value: Any, context: Context) -> int:
    if hasattr(value, '__index__'):
      return value.__index__()
    if isinstance(value, int):
      return value
    if not self.strict and isinstance(value, str):
      try:
        return int(value)
      except ValueError:
        pass  # fallthrough
    raise context.type_error(f'expected integer, got {type_repr(type(value))}')

  to_python = from_python


class StringConverter(Converter):

  def from_python(self, value: Any, context: Context) -> str:
    if isinstance(value, str):
      return value
    raise context.type_error(f'expected str, got {type_repr(type(value))}')

  to_python = from_python


class FloatConverter(_PodConverter):

  def from_python(self, value: Any, context: Context) -> float:
    if isinstance(value, (float, int)):
      return float(value)
    if not self.strict and isinstance(value, str):
      try:
        return float(value)
      except ValueError:
        pass  # fallthrough
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
    decimal_context = self._get_decimal_context(context)
    return str(decimal_context.create_decimal(value))

  def to_python(self, value: str, context: Context) -> decimal.Decimal:
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
    errors = []
    tracebacks = []
    is_debug = _get_log_level(logger) >= logging.DEBUG
    for type_ in args:
      if type_ == type(None): continue
      try:
        return getattr(context.fork(type_, value), method)()
      except ConversionTypeError as exc:
        errors.append(f'{type_repr(type_)}: {exc}')
        if is_debug:
          tracebacks.append(traceback.format_exc())
    if is_debug:
      logger.debug(
        f'Error converting `{type_repr(context.type)}` ({method}). This message is logged in '
        f'conjunction with a ConversionTypeError to provide information about the tracebacks '
        f'that have been caught when converting the individiual union members. This might not '
        f'indicate an error in the program if the exception is handled.\n'
        + '\n'.join(tracebacks))
    errors_text = '\n'.join(errors)
    raise context.type_error(_indent_exc(
      f'expected {type_repr(context.type)}, got {type_repr(type(value))}\n{errors_text}'))

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


@dataclass
class _FieldConversionData:
  name: str
  type: Type
  metadata: FieldMetadata
  target: List[str]

  @property
  def immediate_target(self) -> str:
    return self.target[-1]


@dataclass
class _ModelConversionData:
  metadata: ModelMetadata
  fields: List['_FieldConversionData']
  targets: List['_FieldConversionData']
  wildcard: Optional['_FieldConversionData']


class ModelConverter(Converter):
  """
  Handles the conversion of data models to and from JSON structures.
  """

  def _get_conversion_data(self, type_: Type) -> _ModelConversionData:
    fields = []
    targets = []
    wildcard = None
    for field in enumerate_fields(type_):
      if field.metadata.derived:
        continue
      if field.metadata.flatten and is_datamodel(field.type):
        for field_data in self._get_conversion_data(field.type).fields:
          field_data.target.append(field.name)
          fields.append(field_data)
        targets.append(_FieldConversionData(field.name, field.type, field.metadata, ['*']))
      elif field.metadata.flatten:
        if not wildcard:
          wildcard = _FieldConversionData(field.name, field.type, field.metadata, [])
      else:
        fields.append(_FieldConversionData(field.name, field.type, field.metadata, ['*']))
    return _ModelConversionData(ModelMetadata.for_type(type_), fields, targets, wildcard)

  def _get_serialize_as(self, context: Context) -> Optional[TypeHint]:
    metadata = ModelMetadata.for_type(context.type)
    if isinstance(metadata.serialize_as, types.FunctionType):
      return metadata.serialize_as()
    return metadata.serialize_as

  def to_python(self, value, context: Context) -> dict:
    serialize_as = self._get_serialize_as(context)
    if serialize_as is not None:
      return context.fork(serialize_as, value).to_python()

    if hasattr(context.type, 'databind_json_load'):
      with context.coerce_errors():
        result = context.type.databind_json_load(value, context)
        if result is not NotImplemented:
          return result

    if not isinstance(value, Mapping):
      raise context.type_error(f'expected {type_repr(context.type)} (as mapping), got {type_repr(type(value))}')

    conversion_data = self._get_conversion_data(context.type)
    targets: Dict[str, Dict[str, Any]] = {'*': {}}
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
    try:
      return context.type(**targets['*'])
    except TypeError as exc:
      raise context.type_error(str(exc))

  def from_python(self, value, context: Context) -> Any:
    serialize_as = self._get_serialize_as(context)
    if serialize_as is not None:
      return context.fork(serialize_as, value).from_python()

    if not isinstance(value, context.type):
      raise context.type_error(f'expected {type_repr(context.type)}, got {type_repr(type(value))}')

    if hasattr(value, 'databind_json_dump'):
      with context.coerce_errors():
        result = value.databind_json_dump(context)
        if result is not NotImplemented:
          return result

    skip_defaults = context.registry.get_option(datamodel, 'skip_defaults', False)
    result = {}  # TODO(NiklasRosenstein): Option to override target conversion type.

    for field in enumerate_fields(context.type):
      if field.metadata.derived:
        continue

      python_value = getattr(value, field.name)
      if (skip_defaults and not field.metadata.required and
          field.has_default() and field.get_default() == python_value):
        continue

      field_value = context.child(
        field.name,
        field.type,
        python_value,
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
    if not hasattr(context.type, '__args__') and hasattr(context.type, '__orig_bases__'):
      # For subclasses of the List generic.
      item_type = next(v.__args__[0] for v in context.type.__orig_bases__ if v.__origin__ in (list, List))
      constructor = context.type
    elif context.type.__origin__ in (list, List):
      # For the List generic.
      item_type = context.type.__args__[0]
      constructor = list
    else:
      raise RuntimeError(f'unsure how to handle type {type_repr(context.type)}')
    if not isinstance(value, Sequence):
      raise context.type_error(f'expected {type_repr(context.type)} (as sequence), got {type_repr(type(value))}')
    result = constructor() if method == 'to_python' else list()
    for index, item in enumerate(value):
      # Note: forwarding the FieldMetadata from the parent to the items.
      child_context = context.child(index, item_type, item, context.field_metadata)
      result.append(getattr(child_context, method)())
    return result

  def from_python(self, value, context):
    return self._do_conversion(value, context, 'from_python')

  def to_python(self, value, context):
    return self._do_conversion(value, context, 'to_python')


class AbstractDateConverter(Converter):

  default_format: DatetimeFormat
  py_type: Type
  truncate = staticmethod(lambda d: d)

  def _get_format(self, context: Context) -> DatetimeFormat:
    formats = context.field_metadata and context.field_metadata.formats or []
    datetime_format = find(lambda x: isinstance(x, DatetimeFormat), formats)
    if not datetime_format:
      string_formats = [x for x in formats if isinstance(x, str)]
      if string_formats:
        datetime_format = create_datetime_format_set('field-formats', string_formats)
    if not datetime_format:
      datetime_format = context.registry.get_option(datetime.datetime, 'format')
    if not datetime_format:
      datetime_format = self.default_format
    return datetime_format

  def to_python(self, value: str, context: Context) -> datetime.datetime:
    if isinstance(value, self.py_type):
      return value
    if not isinstance(value, str):
      raise context.type_error(f'expected {type_repr(context.type)} (as string), got {type_repr(type(value))}')
    formatter = self._get_format(context)
    try:
      return self.truncate(formatter.parse(value))
    except ValueError as exc:
      raise context.value_error(str(exc))

  def from_python(self, value: str, context: Context) -> datetime.datetime:
    if not isinstance(value, self.py_type):
      raise context.type_error(f'expected {type_repr(context.type)} (as string), got {type_repr(type(value))}')
    formatter = self._get_format(context)
    try:
      return formatter.format(value)
    except ValueError as exc:
      raise context.value_error(str(exc))


class DatetimeConverter(AbstractDateConverter):

  default_format = Iso8601()
  py_type = datetime.datetime


class DateConverter(AbstractDateConverter):

  default_format = create_datetime_format_set('default', ['%Y-%m-%d'])
  py_type = datetime.date
  truncate = staticmethod(lambda d: d.date())


class DurationConverter(Converter):

  def from_python(self, value: Duration, context: Context) -> str:
    if not isinstance(value, context.type):
      raise context.type_error(f'expected {type_repr(context.type)}, got {type_repr(type(value))}')
    return str(value)

  def to_python(self, value: str, context: Context) -> Duration:
    if not isinstance(value, str):
      raise context.type_error(f'expected {type_repr(context.type)} (as string), got {type_repr(type(value))}')
    try:
      return Duration.parse(value)
    except ValueError as exc:
      raise context.value_error(str(exc))


class UnionConverter(Converter):

  def from_python(self, value, context):
    metadata = UnionMetadata.for_type(context.type)
    if metadata.container:
      if not isinstance(value, context.type):
        raise context.type_error(f'expected {type_repr(context.type)}, got {type_repr(type(value))}')
      type_name = getattr(value, metadata.type_field)
      member_value = getattr(value, type_name)
      member_type = metadata.resolver.type_for_name(type_name)

    else:
      member_value = value
      member_type = type(value)
      try:
        type_name = metadata.resolver.name_for_type(member_type)
      except UnionTypeError as exc:
        raise context.value_error(f'unknown member {type_repr(type(value))} for union {type_repr(context.type)}')

    result = {metadata.type_key: type_name}

    if metadata.flat:
      next_context = context.fork(member_type, member_value)
    else:
      next_context = context.child(type_name, member_type, member_value, context.field_metadata)

    result_member = next_context.from_python()
    if metadata.flat:
      result.update(result_member)
    else:
      result[type_name] = result_member

    return result

  def to_python(self, value, context):
    if not isinstance(value, Mapping):
      raise context.type_error(f'expected {type_repr(context.type)} (as mapping), got {type_repr(type(value))}')
    metadata = UnionMetadata.for_type(context.type)
    if metadata.type_key not in value:
      raise context.type_error(f'missing {metadata.type_key!r} to convert {type_repr(context.type)}')

    value = dict(value)
    type_name = value.pop(metadata.type_key)
    try:
      type_ = metadata.resolver.type_for_name(type_name)
    except UnionTypeError as exc:
      raise context.value_error(f'unknown member {type_name!r} for union {type_repr(context.type)}')

    if metadata.flat:
      next_context = context.fork(type_, value)
    else:
      if type_name not in value:
        raise context.value_error(f'missing {type_name!r} key to convert {type_repr(context.type)}')
      remaining_keys = set(value.keys()) - set([type_name])
      if remaining_keys:
        raise context.value_error(f'additional keys in nested union type {type_repr(context.type)} not permitted: {remaining_keys}')
      next_context = context.child(type_name, type_, value[type_name], context.field_metadata)

    result = next_context.to_python()
    if metadata.container:
      return context.type(type_name, result)

    return result


def register_json_converters(registry: Registry, strict: bool = True) -> None:
  """
  Register the JSON converts to the specified *registry*.

  # Arguments
  registry (Registry): The registry to register the converters to.
  strict (bool): Enable or disable strict mode for converters (default: True). In
    non-strict mode, converters of plain-old-datatypes can accept a string additionally
    to the closest JSON type.
  """

  registry.register_converter(bool, BoolConverter(strict))
  registry.register_converter(int, IntConverter(strict))
  registry.register_converter(str, StringConverter())
  registry.register_converter(float, FloatConverter(strict))
  registry.register_converter(List, ArrayConverter())
  registry.register_converter(Dict, ObjectConverter())
  registry.register_converter(decimal.Decimal, DecimalConverter())
  registry.register_converter(enum.Enum, EnumConverter())
  registry.register_converter(datetime.date, DateConverter())
  registry.register_converter(datetime.datetime, DatetimeConverter())
  registry.register_converter(Duration, DurationConverter())
  registry.register_converter(datamodel, ModelConverter())
  registry.register_converter(uniontype, UnionConverter())
  registry.register_converter(Union, MixtypeConverter())
