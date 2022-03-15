
from ast import And
import base64
import typing as t

import typeapi
from databind.core.context import Context
from databind.core.converter import Converter
from databind.core.settings import Strict
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
      raise ctx.error(f'unable to {self.direction.name.lower()} {source_type.__name__} -> {target_type.__name__}')
    try:
      return adapter(ctx.value)
    except ValueError as exc:
      raise ctx.error(str(exc)) from exc
