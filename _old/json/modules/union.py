
import typing as t
from databind.core import annotations as A, BaseType, Context, ConversionError, Converter, Direction, UnionType
from databind.core.mapper.location import Location
from databind.core.types.adapter import TypeContext


class UnionConverter(Converter):

  def _get_deserialize_member_name(self, value: t.Mapping, style: A.union.Style, discriminator_key: str, location: Location) -> str:
    """ Identify the name of the union member of the given serialized *value* and return it.
    How that name is determined depends on the *style*. """

    if style in (A.union.Style.nested, A.union.Style.flat):
      if discriminator_key not in value:
        raise ConversionError(f'missing discriminator key {discriminator_key!r}', location)
      member_name = value[discriminator_key]
    elif style == A.union.Style.keyed:
      if len(value) != 1:
        raise ConversionError(f'expected exactly one key to act as the discriminator, got {len(value)} key(s)', location)
      member_name = next(iter(value))
    else:
      assert False, style

    return member_name

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, UnionType)

    fallback = ctx.get_annotation(A.union) or A.union()
    style = ctx.type.style or fallback.style or UnionType.DEFAULT_STYLE
    discriminator_key = ctx.type.discriminator_key or fallback.discriminator_key or UnionType.DEFAULT_DISCRIMINATOR_KEY
    is_deserialize = ctx.direction == Direction.deserialize

    if is_deserialize:
      if not isinstance(ctx.value, t.Mapping):
        raise ctx.type_error(expected=t.Mapping)
      member_name = self._get_deserialize_member_name(ctx.value, style, discriminator_key, ctx.location)
      member_type = ctx.type.subtypes.get_type_by_name(member_name, ctx.type_hint_adapter)
      assert isinstance(member_type, BaseType), f'"{type(ctx.type.subtypes).__name__}" returned member_type must '\
          f'be BaseType, got "{type(member_type).__name__}"'
    else:
      member_type = TypeContext(ctx.type_hint_adapter).adapt_type_hint(type(ctx.value))
      member_name = ctx.type.subtypes.get_type_name(member_type, ctx.type_hint_adapter)

    nesting_key = ctx.type.nesting_key or member_name
    type_hint = member_type

    if is_deserialize:
      if style == A.union.Style.nested:
        if nesting_key not in ctx.value:
          raise ConversionError(f'missing union value key {nesting_key!r}', ctx.location)
        child_context = ctx.push(type_hint, ctx.value[nesting_key], nesting_key, ctx.field)
      elif style == A.union.Style.flat:
        child_context = ctx.push(type_hint, dict(ctx.value), None, ctx.field)
        t.cast(t.Dict, child_context.value).pop(discriminator_key)
      elif style == A.union.Style.keyed:
        child_context = ctx.push(type_hint, ctx.value[member_name], member_name, ctx.field)
      else:
        raise RuntimeError(f'bad style: {style!r}')
    else:
      child_context = ctx.push(type_hint, ctx.value, None, ctx.field)

    result = child_context.convert()

    if is_deserialize:
      return result
    else:
      if style == A.union.Style.nested:
        result = {discriminator_key: member_name, member_name: result}
      elif style == A.union.Style.flat:
        if not isinstance(result, t.MutableMapping):
          raise RuntimeError(f'union.Style.flat is not supported for non-object member types')
        result[discriminator_key] = member_name
      elif style == A.union.Style.keyed:
        if not isinstance(result, t.MutableMapping):
          raise RuntimeError(f'union.Style.keyed is not supported for non-object member types')
        result = {member_name: result}
      else:
        raise RuntimeError(f'bda style: {style!r}')

    return result
