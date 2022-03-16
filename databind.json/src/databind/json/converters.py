
import base64
import decimal
from email.errors import NonASCIILocalPartDefect
import enum
import typing as t

import typeapi
from databind.core.context import Context
from databind.core.converter import Converter, ConversionError
from databind.core.settings import Alias, Precision, Strict, get_highest_setting
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
      raise ConversionError(ctx, f'expected string, got {typeapi.type_repr(ctx.value.__class__)}')

    else:
      if not isinstance(ctx.value, decimal.Decimal):
        raise ConversionError(ctx, f'expected decimal.Decimal, got {typeapi.type_repr(ctx.value.__class__)}')
      return str(ctx.value)


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
    hint = typeapi.of(typeapi.get_type_hints(enum_type).get(member_name))
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
        raise ConversionError(ctx, f'expected {ctx.datatype} but found {value.__class__.__name__}')
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
          raise ConversionError(ctx, f'expected int but found {value.__class__.__name__}')
        try:
          return enum_type(value)
        except ValueError as exc:
          raise ConversionError(ctx, str(exc))
      if issubclass(enum_type, enum.Enum):
        if not isinstance(value, str):
          raise ConversionError(ctx, f'expected string but found {value.__class__.__name__}')
        for enum_value in enum_type:
          alias = self._discover_alias(enum_type, enum_value.name)
          if alias and value in alias.aliases:
            return enum_value
        try:
          return enum_type[value]
        except KeyError:
          raise ConversionError(ctx, f'{value!r} is not a member of enumeration {ctx.datatype}')
      assert False, enum_type


class OptionalConverter(Converter):

  def convert(self, ctx: Context) -> t.Any:
    if not isinstance(ctx.datatype, typeapi.Union) or type(None) not in ctx.datatype.types:
      raise NotImplementedError
    if ctx.value is None:
      return None
    types = tuple(t for t in ctx.datatype.types if t is not type(None))
    if len(types) == 1:
      datatype = types[0]
    else:
      datatype = typeapi.Union(types)
    return ctx.spawn(ctx.value, datatype, None).convert()
