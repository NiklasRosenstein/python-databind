
"""
Provides the #ObjectTypeModule that implements the de/serialization of JSON payloads for databind
schemas (see #databind.core.schema).
"""

import typing as t
from databind.core import annotations as A
from databind.core.api import Context, ConversionError, Direction, IConverter, Context
from databind.core.types import ObjectType


class ObjectTypeConverter(IConverter):

  def _serialize(self, ctx: Context, type_: ObjectType) -> t.Dict[str, t.Any]:
    skip_default_values = True

    if not isinstance(ctx.value, type_.schema.python_type):
      raise ctx.type_error(expected=type_.schema.python_type)

    groups: t.Dict[str, t.Dict[str, t.Any]] = {}
    for field in type_.schema.fields.values():
      if not field.flat:
        continue
      value = getattr(ctx.value, field.name)
      if skip_default_values and value == field.get_default():
        continue
      groups[field.name] = ctx.push(field.type, value, field.name, field).convert()

    result: t.Dict[str, t.Any] = {}
    for flat_field in type_.schema.flat_fields():
      alias = (flat_field.field.aliases or [flat_field.field.name])[0]
      if flat_field.group == '$':
        value = getattr(ctx.value, flat_field.field.name)
        if skip_default_values and value != flat_field.field.get_default():
          result[alias] = ctx.push(flat_field.field.type, value, flat_field.field.name, flat_field.field).convert()
      elif alias in groups[flat_field.group]:
        # May not be contained if we skipped default values.
        result[alias] = groups[flat_field.group][alias]

    # TODO (@NiklasRosenstein): Support flat MapType() field

    return result

  def _deserialize(self, ctx: Context, type_: ObjectType) -> t.Any:
    enable_unknowns = ctx.settings.get(A.enable_unknowns)
    typeinfo = ctx.get_annotation(A.typeinfo)

    if not isinstance(ctx.value, t.Mapping):
      raise ctx.type_error(expected=t.Mapping)

    groups: t.Dict[str, t.Dict[str, t.Any]] = {'$': {}}

    # Collect keys into groups.
    used_keys: t.Set[str] = set()
    for flat_field in type_.schema.flat_fields():
      aliases = flat_field.field.aliases or [flat_field.field.name]
      for alias in aliases:
        if alias in ctx.value:
          value = ctx.value[alias]
          groups.setdefault(flat_field.group, {})[flat_field.field.name] = \
            ctx.push(flat_field.field.type, value, flat_field.field.name, flat_field.field).convert()
          used_keys.add(alias)
          break

    # Move captured groups into the root group ($).
    for group, values in groups.items():
      if group == '$': continue
      field = type_.schema.fields[group]
      groups['$'][group] = ctx.push(field.type, values, group, field).convert()

    if not enable_unknowns or (enable_unknowns and enable_unknowns.callback):
      unused_keys = ctx.value.keys() - used_keys
      if unused_keys and not enable_unknowns:
        raise ConversionError(f'unknown keys found while deserializing {ctx.type}: {unused_keys}', ctx.location)
      elif unused_keys and enable_unknowns and enable_unknowns.callback:
        enable_unknowns.callback(ctx, set(unused_keys))

    # TODO (@NiklasRosenstein): Support flat MapType() field

    try:
      return ((typeinfo.deserialize_as if typeinfo else None) or type_.schema.python_type)(**groups['$'])
    except TypeError as exc:
      raise ctx.error(str(exc))

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, ObjectType)
    if ctx.direction == Direction.serialize:
      return self._serialize(ctx, ctx.type)
    elif ctx.direction == Direction.deserialize:
      return self._deserialize(ctx, ctx.type)
    assert False
