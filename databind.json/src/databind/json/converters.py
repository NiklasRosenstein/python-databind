
import base64
import collections.abc
import datetime
import decimal
import enum
import typing as t

import typeapi
from databind.core.context import Context
from databind.core.converter import Converter, ConversionError
from databind.core.settings import Alias, DateFormat, Precision, Strict, get_highest_setting
from databind.json.direction import Direction


def _int_lossless(v: float) -> int:
  """ Convert *v* to an integer only if the conversion is lossless, otherwise raise an error. """

  assert v % 1.0 == 0.0, f'expected int, got {v!r}'
  return int(v)


def _bool_from_str(s: str) -> bool:
  """ Converts *s* to a boolean value based on common truthy keywords. """

  if s.lower() in ('yes', 'true', 'on', 'enabled'):
    return True
  if s.lower() in ('no', 'false', 'off', 'disabled'):
    return True
  raise ValueError(f'not a truthy keyword: {s!r}')


class AnyConverter(Converter):
  """ A converter for #typing.Any and #object typed values, which will return them unchanged in any case. """

  def convert(self, ctx: Context) -> t.Any:
    is_any_type = (
      isinstance(ctx.datatype, typeapi.Any) or
      isinstance(ctx.datatype, typeapi.Type) and ctx.datatype.type is object)
    if is_any_type:
      return ctx.value
    raise NotImplementedError


class CollectionConverter(Converter):

  def __init__(self, direction: Direction, json_collection_type: t.Type[collections.abc.Collection] = list) -> None:
    self.direction = direction
    self.json_collection_type = json_collection_type

  def convert(self, ctx: Context) -> t.Any:
    if not isinstance(ctx.datatype, typeapi.Type) or not issubclass(ctx.datatype.type, collections.abc.Collection):
      raise NotImplementedError

    if ctx.datatype.nparams != 1:
      # TODO (@NiklasRosenstein): Look into the type's bases and find the mapping base class while keeping
      # track of type parameter values.
      raise NotImplementedError

    python_type = ctx.datatype.type
    item_type = ctx.datatype.args[0] if ctx.datatype.args else t.Any
    values: t.Iterable = (ctx.spawn(val, item_type, idx).convert() for idx, val in enumerate(ctx.value))

    if self.direction == Direction.SERIALIZE:
      if not isinstance(ctx.value, python_type):
        raise ConversionError.expected(ctx, python_type)
      return self.json_collection_type(values)  # type: ignore[call-arg]

    else:
      if not isinstance(ctx.value, t.Collection) or isinstance(ctx.value, (str, bytes, bytearray, memoryview)):
        raise ConversionError.expected(ctx, collections.abc.Collection)
      if python_type != list:
        values = list(values)
      try:
        return python_type(values)  # type: ignore[call-arg]
      except TypeError:
        # We assume that the native list is an appropriate placeholder for whatever specific Collection type
        # was chosen in the value's datatype.
        return values


class DatetimeConverter(Converter):
  """ A converter for #datetime.datetime, #datetime.date and #datetime.time that represents the serialized form as
  strings formatted using the #nr.util.date module. The converter respects the #DateFormat setting. """

  DEFAULT_DATE_FMT = DateFormat('.ISO_8601')
  DEFAULT_TIME_FMT = DEFAULT_DATE_FMT
  DEFAULT_DATETIME_FMT = DEFAULT_DATE_FMT

  def __init__(self, direction: Direction) -> None:
    self.direction = direction

  def convert(self, ctx: Context) -> t.Any:
    if not isinstance(ctx.datatype, typeapi.Type):
      raise NotImplementedError

    date_type = ctx.datatype.type
    if date_type not in (datetime.date, datetime.time, datetime.datetime):
      raise NotImplementedError

    datefmt = ctx.get_setting(DateFormat) or (
      self.DEFAULT_DATE_FMT if date_type == datetime.date else
      self.DEFAULT_TIME_FMT if date_type == datetime.time else
      self.DEFAULT_DATETIME_FMT if date_type == datetime.datetime else None)
    assert datefmt is not None

    if self.direction == Direction.DESERIALIZE:
      if isinstance(ctx.value, date_type):
        return ctx.value
      elif isinstance(ctx.value, str):
        try:
          dt = datefmt.parse(date_type, ctx.value)
        except ValueError as exc:
          raise ConversionError(ctx, str(exc))
        assert isinstance(dt, date_type)
        return dt
      raise ConversionError.expected(ctx, date_type, type(ctx.value))

    else:
      if not isinstance(ctx.value, date_type):
        raise ConversionError.expected(ctx, date_type, type(ctx.value))
      return datefmt.format(ctx.value)


class DecimalConverter(Converter):
  """ A converter for #decimal.Decimal values to and from JSON as strings. """

  def __init__(self, direction: Direction, strict_by_default: bool = True) -> None:
    self.direction = direction
    self.strict_by_default = strict_by_default

  def convert(self, ctx: Context) -> t.Any:
    if not isinstance(ctx.datatype, typeapi.Type) or not issubclass(ctx.datatype.type, decimal.Decimal):
      raise NotImplementedError

    strict = ctx.get_setting(Strict) or Strict(self.strict_by_default)
    precision = ctx.get_setting(Precision)
    context = precision.to_decimal_context() if precision else None

    if self.direction == Direction.DESERIALIZE:
      if (not strict.enabled and isinstance(ctx.value, (int, float))) or isinstance(ctx.value, str):
        return decimal.Decimal(ctx.value, context)
      raise ConversionError.expected(ctx, str, type(ctx.value))

    else:
      if not isinstance(ctx.value, decimal.Decimal):
        raise ConversionError.expected(ctx, decimal.Decimal, type(ctx.value))
      return str(ctx.value)


class DurationConverter(Converter):
  """ A converter for #nr.util.date.duration in ISO 8601 duration format. """

  def __init__(self, direction: Direction) -> None:
    self.direction = direction

  def convert(self, ctx: Context) -> t.Any:
    from nr.util.date import duration
    if not isinstance(ctx.datatype, typeapi.Type) or not issubclass(ctx.datatype.type, duration):
      raise NotImplementedError

    if self.direction == Direction.SERIALIZE:
      if not isinstance(ctx.value, duration):
        raise ConversionError.expected(ctx, duration)
      return str(ctx.value)

    else:
      if not isinstance(ctx.value, str):
        raise ConversionError.expected(ctx, str)
      try:
        return duration.parse(ctx.value)
      except ValueError as exc:
        raise ConversionError(ctx, str(exc))


class EnumConverter(Converter):
  """ JSON converter for enum values.

  Converts #enum.IntEnum values to integers and #enum.Enum values to strings. Note that combined integer flags
  are not supported and cannot be serializ

  #Alias#es on the type annotation of an enum field are considered as aliases for the field name to be used
  in the value's serialized form as opposed to its value name defined in code.

  Example:

  ```py
  import enum, typing
  from databind.core.settings import Alias

  class Pet(enum.Enum):
    CAT = enum.auto()
    DOG = enum.auto()
    LION: typing.Annotated[int, Alias('KITTY')] = enum.auto()
  ```
  """

  def __init__(self, direction: Direction) -> None:
    self.direction = direction

  def _discover_alias(self, enum_type: t.Type[enum.Enum], member_name: str) -> t.Optional[Alias]:
    # TODO (@NiklasRosenstein): Take into account annotations of the base classes?
    hint = typeapi.of(typeapi.get_annotations(enum_type).get(member_name))
    if isinstance(hint, typeapi.Annotated):
      return get_highest_setting(s for s in hint.metadata if isinstance(s, Alias))
    return None

  def convert(self, ctx: Context) -> t.Any:
    if not isinstance(ctx.datatype, typeapi.Type):
      raise NotImplementedError
    if not issubclass(ctx.datatype.type, enum.Enum):
      raise NotImplementedError

    value = ctx.value
    enum_type = ctx.datatype.type

    if self.direction == Direction.SERIALIZE:
      if type(value) is not enum_type:
        raise ConversionError.expected(ctx, enum_type, type(value))
      if issubclass(enum_type, enum.IntEnum):
        return value.value
      if issubclass(enum_type, enum.Enum):
        alias = self._discover_alias(enum_type, value.name)
        if alias and alias.aliases:
          return alias.aliases[0]
        return value.name
      assert False, enum_type

    else:
      if issubclass(enum_type, enum.IntEnum):
        if not isinstance(value, int):
          raise ConversionError.expected(ctx, int, type(value))
        try:
          return enum_type(value)
        except ValueError as exc:
          raise ConversionError(ctx, str(exc))
      if issubclass(enum_type, enum.Enum):
        if not isinstance(value, str):
          raise ConversionError.expected(ctx, str, type(value))
        for enum_value in enum_type:
          alias = self._discover_alias(enum_type, enum_value.name)
          if alias and value in alias.aliases:
            return enum_value
        try:
          return enum_type[value]
        except KeyError:
          raise ConversionError(ctx, f'{value!r} is not a member of enumeration {ctx.datatype}')
      assert False, enum_type


class MappingConverter(Converter):

  def __init__(self, direction: Direction, json_mapping_type: t.Type[collections.abc.Mapping] = dict) -> None:
    self.direction = direction
    self.json_mapping_type = json_mapping_type

  def convert(self, ctx: Context) -> t.Any:
    if not isinstance(ctx.datatype, typeapi.Type) or not issubclass(ctx.datatype.type, collections.abc.Mapping):
      raise NotImplementedError

    if ctx.datatype.nparams != 2:
      # TODO (@NiklasRosenstein): Look into the type's bases and find the mapping base class while keeping
      # track of type parameter values.
      raise NotImplementedError

    if ctx.datatype.args is None:
      key_type, value_type = t.Any, t.Any
    else:
      key_type, value_type = ctx.datatype.args

    if not isinstance(ctx.value, collections.abc.Mapping):
      raise ConversionError.expected(ctx, collections.abc.Mapping)

    result = {}
    for key, value in ctx.value.items():
      value = ctx.spawn(value, value_type, key).convert()
      key = ctx.spawn(key, key_type, f'Key({key!r})').convert()
      result[key] = value

    if self.direction == Direction.DESERIALIZE and ctx.datatype.type != dict:
      # We assume that the runtime type is constructible from a plain dictionary.
      try:
        return ctx.datatype.type(result)  # type: ignore[call-arg]
      except TypeError:
        # We expect this exception to occur for example if the annotated type is an abstract class like
        # collections.abc.Mapping; in which case we just assume that "dict' is a fine type to return.
        return result
    elif self.direction == Direction.SERIALIZE and self.json_mapping_type != dict:
      # Same for the JSON output type.
      return self.json_mapping_type(result)  # type: ignore[call-arg]

    return result


class OptionalConverter(Converter):

  def convert(self, ctx: Context) -> t.Any:
    if not isinstance(ctx.datatype, typeapi.Union) or not ctx.datatype.has_none_type():
      raise NotImplementedError
    if ctx.value is None:
      return None
    return ctx.spawn(ctx.value, ctx.datatype.without_none_type(), None).convert()


class PlainDatatypeConverter(Converter):
  """ A converter for the plain datatypes #bool, #bytes, #int, #str and #float.

  Arguments:
    direction (Direction): The direction in which to convert (serialize or deserialize).
    strict_by_default (bool): Whether to use strict type conversion on values by default if no other
      information on strictness is given. This defaults to `True`. With strict conversion enabled,
      loss-less type conversions are disabled (such as casting a string to an integer). Note that
      serialization is _always_ strict, only the deserialization is controlled with this option or
      the #Strict setting.
  """

  # Map for (source_type, target_type)
  _strict_adapters: t.Dict[t.Tuple[t.Type, t.Type], t.Callable[[t.Any], t.Any]] = {
    (bytes, bytes):   lambda d: base64.b64encode(d).decode('ascii'),
    (str, bytes):     base64.b64decode,
    (str, str):       str,
    (int, int):       int,
    (float, float):   float,
    (int, float):     float,
    (float, int):     _int_lossless,
    (bool, bool):     bool,
  }

  # Used only during deserialization if the #fieldinfo.strict is disabled.
  _nonstrict_adapters = _strict_adapters.copy()
  _nonstrict_adapters.update({
    (str, int):       int,
    (str, float):     float,
    (str, bool):      _bool_from_str,
    (int, str):       str,
    (float, str):     str,
    (bool, str):      str,
  })

  def __init__(self, direction: Direction, strict_by_default: bool = True) -> None:
    self.direction = direction
    self.strict_by_default = strict_by_default

  def convert(self, ctx: Context) -> t.Any:
    if not isinstance(ctx.datatype, typeapi.Type):
      raise NotImplementedError
    if ctx.datatype.type not in {k[0] for k in self._strict_adapters}:
      raise NotImplementedError

    source_type = type(ctx.value)
    target_type = ctx.datatype.type
    strict = (
      (ctx.get_setting(Strict) or Strict(self.strict_by_default))
      if self.direction == Direction.DESERIALIZE else
      Strict(True))
    adapters = (self._strict_adapters if strict.enabled else self._nonstrict_adapters)
    adapter = adapters.get((source_type, target_type))

    if adapter is None:
      msg = f'unable to {self.direction.name.lower()} {source_type.__name__} -> {target_type.__name__}'
      raise ConversionError(ctx, msg)

    try:
      return adapter(ctx.value)
    except ValueError as exc:
      raise ConversionError(ctx, str(exc)) from exc


# class SchemaConverter(Converter):
#   """ Converter for type hints that can be adopted to a schema definition with #databind.core.schema.of(). """

#   def _serialize(self, ctx: Context) -> t.Dict[str, t.Any]:
#     skip_default_values = True

#     if not isinstance(ctx.value, type_.schema.python_type):
#       raise ctx.type_error(expected=type_.schema.python_type)

#     groups: t.Dict[str, t.Dict[str, t.Any]] = {}
#     for field in type_.schema.fields.values():
#       if not field.flat:
#         continue
#       value = getattr(ctx.value, field.name)
#       if skip_default_values and value == field.get_default():
#         continue
#       groups[field.name] = ctx.push(field.type, value, field.name, field).convert()

#     result: t.Dict[str, t.Any] = {}
#     flattened = type_.schema.flattened()
#     for name, flat_field in flattened.fields.items():
#       alias = (flat_field.field.aliases or [name])[0]
#       if not flat_field.group:
#         value = getattr(ctx.value, name)
#         if skip_default_values and value != flat_field.field.get_default():
#           result[alias] = ctx.push(flat_field.field.type, value, name, flat_field.field).convert()
#       elif alias in groups[flat_field.group or '$']:
#         # May not be contained if we skipped default values.
#         result[alias] = groups[flat_field.group or '$'][alias]

#     # Explode values from the remainder field into the result.
#     if flattened.remainder_field:
#       assert isinstance(flattened.remainder_field.type, MapType)
#       remnants = ctx.push(flattened.remainder_field.type, getattr(ctx.value, flattened.remainder_field.name), None, flattened.remainder_field).convert()
#       for key, value in remnants.items():
#         if key in result:
#           raise ctx.error(f'key {key!r} of remainder field {flattened.remainder_field.name!r} cannot be exploded '
#             'into resulting JSON object because of a conflict.')
#         result[key] = value

#     return result

#   def _deserialize(self, ctx: Context) -> t.Any:
#     enable_unknowns = ctx.settings.get(A.enable_unknowns)
#     typeinfo = ctx.get_annotation(A.typeinfo)

#     if not isinstance(ctx.value, t.Mapping):
#       raise ctx.type_error(expected=t.Mapping)

#     groups: t.Dict[str, t.Dict[str, t.Any]] = {'$': {}}

#     # Collect keys into groups.
#     used_keys: t.Set[str] = set()
#     flattened = type_.schema.flattened()
#     for name, flat_field in flattened.fields.items():
#       aliases = flat_field.field.aliases or [name]
#       for alias in aliases:
#         if alias in ctx.value:
#           value = ctx.value[alias]
#           groups.setdefault(flat_field.group or '$', {})[name] = \
#             ctx.push(flat_field.field.type, value, name, flat_field.field).convert()
#           used_keys.add(alias)
#           break

#     # Move captured groups into the root group ($).
#     for group, values in groups.items():
#       if group == '$': continue
#       field = type_.schema.fields[group]
#       groups['$'][group] = ctx.push(field.type, values, group, field).convert()

#     # Collect unknown fields into the remainder field if there is one.
#     if flattened.remainder_field:
#       assert isinstance(flattened.remainder_field.type, MapType)
#       remanants = {k: ctx.value[k] for k in ctx.value.keys() - used_keys}
#       groups['$'][flattened.remainder_field.name] = ctx.push(flattened.remainder_field.type, remanants, None, flattened.remainder_field).convert()
#       used_keys.update(ctx.value.keys())

#     if not enable_unknowns or (enable_unknowns and enable_unknowns.callback):
#       unused_keys = ctx.value.keys() - used_keys
#       if unused_keys and not enable_unknowns:
#         raise ConversionError(f'unknown keys found while deserializing {ctx.type}: {unused_keys}', ctx.location)
#       elif unused_keys and enable_unknowns and enable_unknowns.callback:
#         enable_unknowns.callback(ctx, set(unused_keys))

#     try:
#       return ((typeinfo.deserialize_as if typeinfo else None) or type_.schema.python_type)(**groups['$'])
#     except TypeError as exc:
#       raise ctx.error(str(exc))

#   def convert(self, ctx: Context) -> t.Any:
#     assert isinstance(ctx.type, ObjectType)

#     try:
#       return with_custom_json_converter.apply_converter(ctx.type.schema.python_type, ctx)
#     except ConversionNotApplicable:
#       pass

#     if ctx.direction == Direction.serialize:
#       return self._serialize(ctx, ctx.type)
#     elif ctx.direction == Direction.deserialize:
#       return self._deserialize(ctx, ctx.type)
#     assert False


class StringifyConverter(Converter):
  """ A useful helper converter that matches on a given type or its subclasses and converts them to a string for
  serialization and deserializes them from a string using the type's constructor. """

  def __init__(self, direction: Direction, type_: t.Type) -> None:
    assert isinstance(type_, type), type_
    self.direction = direction
    self.type_ = type_

  def convert(self, ctx: Context) -> t.Any:
    if not isinstance(ctx.datatype, typeapi.Type) or not issubclass(ctx.datatype.type, self.type_):
      raise NotImplementedError

    if self.direction == Direction.DESERIALIZE:
      if not isinstance(ctx.value, str):
        raise ConversionError.expected(ctx, str)
      try:
        return self.type_(ctx.value)
      except (TypeError, ValueError) as exc:
        raise ConversionError(ctx, str(exc))

    else:
      if not isinstance(ctx.value, ctx.datatype.type):
        raise ConversionError.expected(ctx, ctx.datatype.type)
      return str(ctx.value)
