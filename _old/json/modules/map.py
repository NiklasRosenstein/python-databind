
import typing as t
from databind.core import Context, Converter, MapType


class MapConverter(Converter):

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, MapType)

    # # Catch subclasses of the typing.Dict generics. The instantiated generic with the type
    # # parameter will be stored in __orig_bases__.
    # dict_base = find_orig_base(context.type, Dict)
    # if dict_base:
    #   key_type, value_type = dict_base.__args__[0], dict_base.__args__[1]
    #   constructor = context.type
    #
    # # Otherwise, catch instances of the typing.List generic.
    # elif getattr(context.type, '__origin__', None) in (dict, Dict):
    #  # For the List generic.
    #  key_type, value_type = context.type.__args__[0], context.type.__args__[1]
    #  constructor = list
    #
    # else:
    #   raise RuntimeError(f'unsure how to handle type {type_repr(context.type)}')

    if not isinstance(ctx.value, t.Mapping):
      raise ctx.type_error(expected=t.Mapping)

    result = dict()  # TODO (@NiklasRosenstein): Check MapType.impl_hint

    for key, value in ctx.value.items():
      if ctx.type.key_type is not None:
        key = ctx.push(ctx.type.key_type, key, f'Key({key!r})', ctx.field).convert()
      if ctx.type.value_type is not None:
        value = ctx.push(ctx.type.value_type, value, key, ctx.field).convert()
      result[key] = value

    return result
