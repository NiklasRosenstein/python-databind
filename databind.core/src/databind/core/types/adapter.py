
import typing as t
import typing_extensions as te


def from_typing(type_hint: t.Any) -> 'BaseType':
  """
  Convert a #typing type hint to an API #TypeHint.
  """

  generic, args = _unpack_type_hint(type_hint)

  # Support custom subclasses of typing generic aliases (e.g. class MyList(t.List[int])
  # or class MyDict(t.Mapping[K, V])). If we find a type like that, we keep a reference
  # to it in "python_type" so we know what we need to construct during deserialization.
  # NOTE (@NiklasRosenstein): We only support a single generic base.
  python_type: t.Optional[t.Type] = None
  generic_bases = find_generic_bases(type_hint)
  if len(generic_bases) == 1:
    python_type = generic
    generic, args = _unpack_type_hint(generic_bases[0])

  if generic is not None:
    generic = _ORIGIN_CONVERSION.get(generic, generic)
    if generic == t.Any:
      return ConcreteType(object)
    elif generic == t.List and len(args) == 1:
      return ListType(from_typing(args[0]), python_type or list)
    elif generic == t.Set and len(args) == 1:
      return SetType(from_typing(args[0]), python_type or set)
    elif generic in (t.Dict, t.Mapping, t.MutableMapping) and len(args) == 2:
      return MapType(from_typing(args[0]), from_typing(args[1]), python_type or generic)
    elif (generic == t.Optional and len(args) == 1) or (generic == t.Union and None in args and len(args) == 2):  # type: ignore
      if len(args) == 1:
        return OptionalType(from_typing(args[0]))
      elif len(args) == 2:
        return OptionalType(from_typing(next(x for x in args if x is not None)))
      else:
        raise ValueError(f'unexpected args for {generic}: {args}')
    elif generic == t.Union and len(args) > 0:
      if len(args) == 1:
        return from_typing(args[0])
      elif type(None) in args:
        return OptionalType(from_typing(t.Union[tuple(x for x in args if x is not type(None))]))
      else:
        return ImplicitUnionType(tuple(from_typing(a) for a in args))
    elif hasattr(te, 'Annotated') and generic == te.Annotated and len(args) >= 2:  # type: ignore
      type_ = from_typing(args[0])
      type_.annotations += args[1:]
      return type_

  if isinstance(type_hint, type):
    return ConcreteType(type_hint)

  raise ValueError(f'unsupported type hint {type_hint!r}')


from .types import BaseType, ConcreteType, ListType, SetType, MapType, OptionalType, ImplicitUnionType
from .utils import _unpack_type_hint, find_generic_bases, _ORIGIN_CONVERSION
