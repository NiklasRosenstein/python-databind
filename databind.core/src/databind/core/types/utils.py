
import sys
import typing as t
import typing_extensions as te
from collections.abc import Mapping as _Mapping, MutableMapping as _MutableMapping

_ORIGIN_CONVERSION = {  # TODO: Build automatically
  list: t.List,
  set: t.Set,
  dict: t.Dict,
  _Mapping: t.Mapping,
  _MutableMapping: t.MutableMapping,
}


def type_repr(typ: t.Any) -> str:
  return t._type_repr(typ)  # type: ignore


def unpack_type_hint(hint: t.Any) -> t.Tuple[t.Optional[t.Any], t.List[t.Any]]:
  """
  Unpacks a type hint into it's origin type and parameters. Returns #None if the
  *hint* does not represent a type or type hint in any way.
  """

  if hasattr(te, '_AnnotatedAlias') and isinstance(hint, te._AnnotatedAlias):  # type: ignore
    return te.Annotated, list((hint.__origin__,) + hint.__metadata__)  # type: ignore

  if hasattr(t, '_SpecialGenericAlias') and isinstance(hint, t._SpecialGenericAlias):  # type: ignore
    return hint.__origin__, []

  if isinstance(hint, t._GenericAlias) or (sys.version_info >= (3, 9) and isinstance(hint, t.GenericAlias)):  # type: ignore
    if sys.version_info >= (3, 9) or hint.__args__ != hint.__parameters__:
      return hint.__origin__, list(hint.__args__)
    else:
      return hint.__origin__, []

  if isinstance(hint, type):
    return hint, []

  if isinstance(hint, t._SpecialForm):
    return hint, []

  return None, []


def find_generic_bases(type_hint: t.Type, generic_type: t.Optional[t.Any] = None) -> t.List[t.Any]:
  """
  This method finds all generic bases of a given type or generic aliases.

  As a reminder, a generic alias is any subclass of #t.Generic that is indexed with type arguments
  or a special alias like #t.List, #t.Set, etc. The type arguments of that alias are propagated
  into the returned generic bases (except if the base is a #t.Generic because that can only accept
  type variables as arguments).

  Examples:

  ```py
  class MyList(t.List[int]):
    ...
  class MyGenericList(t.List[T]):
    ...
  assert find_generic_bases(MyList) == [t.List[int]]
  assert find_generic_bases(MyGenericList) == [t.List[T]]
  assert find_generic_bases(MyGenericList[int]) == [t.List[int]]
  ```
  """

  type_, args = unpack_type_hint(type_hint)
  params = getattr(type_, '__parameters__', [])
  bases = getattr(type_, '__orig_bases__', [])

  generic_choices: t.Tuple[t.Any, ...] = (generic_type,) if generic_type else ()
  if generic_type and generic_type.__origin__:
    generic_choices += (generic_type.__origin__,)

  result: t.List[t.Any] = []
  for base in bases:
    origin = getattr(base, '__origin__', None)
    if (not generic_type and origin) or \
       (base == generic_type or origin in generic_choices):
      result.append(base)

  for base in bases:
    result += find_generic_bases(base, generic_type)

  # Replace type parameters.
  for idx, hint in enumerate(result):
    origin = _ORIGIN_CONVERSION.get(hint.__origin__, hint.__origin__)
    if origin == t.Generic:  # type: ignore
      continue
    result[idx] = populate_type_parameters(origin, hint.__args__, params, args)

  return result


def populate_type_parameters(
  generic_type: t.Any,
  generic_args: t.List[t.Any],
  parameters: t.List[t.Any],
  arguments: t.List[t.Any]) -> t.Any:
  """
  Given a generic type and it's aliases (for example from `__parameters__`), this function will return an
  alias for the generic type where occurrences of type variables from *parameters* are replaced with actual
  type arguments from *arguments*.

  Example:

  ```py
  assert populate_type_parameters(t.List, [T], [T], [int]) == t.List[int]
  assert populate_type_parameters(t.Mapping, [K, V], [V], [str]) == t.Mapping[K, str]
  ```
  """

  new_args = []
  for type_arg in generic_args:
    arg_index = parameters.index(type_arg) if type_arg in parameters else -1
    if arg_index >= 0 and arg_index < len(arguments):
      new_args.append(arguments[arg_index])
    else:
      new_args.append(type_arg)
  return generic_type[tuple(new_args)]
