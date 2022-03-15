
"""
Provides the #PlainDatatypeModule which contains converters for plain datatypes.
"""

import base64
import typing as t
from databind.core import annotations as A, ConcreteType, Context, Direction, Converter


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


class PlainJsonConverter(Converter):
  """
  Converter for the following plain types:

  * #bool
  * #int
  * #float
  * #str

  Non-strict handling will allow conversion of values from str to other plain types during
  deserialization but not during serialization.
  """

  # Map for (source_type, target_type)
  _strict_adapters: t.Dict[t.Tuple[t.Type, t.Type], t.Callable[[t.Any], t.Any]] = {
    (bytes, bytes): lambda d: base64.b64encode(d).decode('ascii'),
    (str, bytes): base64.b64decode,
    (str, str): str,
    (int, int): int,
    (float, float): float,
    (int, float): float,
    (float, int): _int_lossless,
    (bool, bool): bool,
  }

  # Used only during deserialization if the #fieldinfo.strict is disabled.
  _nonstrict_adapters = _strict_adapters.copy()
  _nonstrict_adapters.update({
    (str, int): int,
    (str, float): float,
    (str, bool): _bool_from_str,
    (int, str): str,
    (float, str): str,
    (bool, str): str,
  })

  def convert(self, ctx: Context) -> t.Any:
    source_type = type(ctx.value)
    assert isinstance(ctx.location.type, ConcreteType)
    target_type = ctx.location.type.type
    fieldinfo = ctx.get_annotation(A.fieldinfo) or A.fieldinfo()
    strict = ctx.direction == Direction.serialize or fieldinfo.strict
    func = (self._strict_adapters if strict else self._nonstrict_adapters)\
        .get((source_type, target_type))
    if func is None:
      raise ctx.error(f'unable to {ctx.direction.name} {source_type.__name__} -> {target_type.__name__}')
    try:
      return func(ctx.value)
    except ValueError as exc:
      raise ctx.error(str(exc))
