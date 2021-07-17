
import typing as t
from databind.core import annotations as A
from databind.core.api import Context, ConversionError, ConverterNotFound, Direction, IConverter
from databind.core.objectmapper import Module
from databind.core.types import AnnotatedType, BaseType, ObjectType, UnionType, from_typing
from nr import preconditions


class UnionTypeModule(Module):

  def get_converter(self, type: BaseType, direction: Direction) -> IConverter:
    if isinstance(type, UnionType):
        return UnionConverter()
    raise ConverterNotFound(type, direction)


class UnionConverter(IConverter):
  """
  Converter for schema's with th
  """

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, UnionType)
    fallback = ctx.mapper.get_global_annotation(A.unionclass) or A.unionclass()
    style = ctx.type.style or fallback.style or UnionType.DEFAULT_STYLE
    discriminator_key = ctx.type.discriminator_key or fallback.discriminator_key or UnionType.DEFAULT_DISCRIMINATOR_KEY

    is_deserialize = ctx.direction == Direction.deserialize

    if is_deserialize:
      if not isinstance(ctx.value, t.Mapping):
        raise ctx.type_error(expected='Object')
      if discriminator_key not in ctx.value:
        raise ConversionError(f'missing discriminator key {discriminator_key!r}', ctx.location)
      member_name = ctx.value[discriminator_key]
      member_type = ctx.type.subtypes.get_type_by_name(member_name)
      assert isinstance(member_type, BaseType), f'"{type(ctx.type.subtypes).__name__}" returned member_type must '\
          f'be BaseType, got "{type(member_type).__name__}"'
    else:
      member_type = from_typing(type(ctx.value))
      member_name = ctx.type.subtypes.get_type_name(member_type)

    type_hint = ctx.mapper.adapt_type_hint(member_type).normalize()

    if is_deserialize:
      if style == A.unionclass.Style.nested:
        if member_name not in ctx.value:
          raise ConversionError(f'missing value key {member_name!r}', ctx.location)
        child_context = ctx.push(type_hint, ctx.value[member_name], member_name, ctx.field)
      elif style == A.unionclass.Style.flat:
        child_context = ctx.push(type_hint, dict(ctx.value), None, ctx.field)
        t.cast(t.Dict, child_context.value).pop(discriminator_key)
      else:
        raise RuntimeError(f'bad style: {style!r}')
    else:
      child_context = ctx.push(type_hint, ctx.value, None, ctx.field)

    result = child_context.convert()

    if is_deserialize:
      return result
    else:
      if style == A.unionclass.Style.nested:
        result = {discriminator_key: member_name, member_name: result}
      else:
        if not isinstance(result, t.MutableMapping):
          raise RuntimeError(f'unionclass.Style.flat is not supported for non-object member types')
        result[discriminator_key] = member_name

    return result
