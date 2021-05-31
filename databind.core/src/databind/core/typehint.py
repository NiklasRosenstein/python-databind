
"""
This module represents a subset of the #typing type hints as a stable API. The concepts exposed by
the #typing module are represented as instances of the #TypeHint subclass (e.g., #Union, #List,
#Map). The purpose of this module is to provide an easy method to introspect type hints.

Use #from_typing() to convert an actual type hint to the stable API and #TypeHint.to_typing() for
the reverse operation.
"""

__all__ = [
  'TypeHint',
  'Concrete',
  'Annotated',
  'Union',
  'Optional',
  'Collection',
  'List',
  'Set',
  'Map',
  'from_typing',
]

import abc
import typing as t
from collections.abc import Mapping as _Mapping, MutableMapping as _MutableMapping
from dataclasses import dataclass
from typing import _type_repr, _GenericAlias  # type: ignore

if t.TYPE_CHECKING:
  from .schema import Schema


class TypeHint(metaclass=abc.ABCMeta):
  """ Base class for an API representation of #typing type hints. """

  def __init__(self) -> None:
    raise TypeError('TypeHint cannot be constructed')

  def __str__(self) -> str:
    return _type_repr(self.to_typing())

  @abc.abstractmethod
  def to_typing(self) -> t.Any:
    """ Convert the type hint back to a #typing representation. """


@dataclass
class Concrete(TypeHint):
  """
  Represents a concrete type, that is an actual Python type, not a typing hint. Note that concrete
  types may be reinterpreted as a #Datamodel by the object mapper, but #from_typing() cannot do
  that because the reinterpretation is up to the object mapper configuration.
  """

  type: t.Type

  def to_typing(self) -> t.Any:
    return self.type


@dataclass
class Annotated(TypeHint):
  """ Represents an annotated type. Nested annotations are usually flattened. """

  type: TypeHint
  annotations: t.Tuple[t.Any, ...]

  def to_typing(self) -> t.Any:
    if not hasattr(t, 'Annotated'):
      raise RuntimeError('this version of Python does not support typing.Annotated')
    return t.Annotated[(self.type,) + self.annotations]  # type: ignore


@dataclass
class Union(TypeHint):
  """ Represents a union of types. Unions never represent optionals, as is the case in typing. """

  types: t.Tuple[TypeHint, ...]

  def to_typing(self) -> t.Any:
    return t.Union[self.types]


@dataclass
class Optional(TypeHint):
  """ Represents an optional type. """

  type: TypeHint

  def to_typing(self) -> t.Any:
    return t.Optional[self.type]


class Collection(TypeHint):
  """ Represents a collection type. This is still abstract. """

  item_type: TypeHint


@dataclass
class List(Collection):
  """ Represents a list type. """

  item_type: TypeHint

  def to_typing(self) -> t.Any:
    return t.List[self.item_type.to_typing()]  # type: ignore


@dataclass
class Set(Collection):
  """ Represents a set type. """

  item_type: TypeHint

  def to_typing(self) -> t.Any:
    return t.Set[self.item_type.to_typing()]  # type: ignore


@dataclass
class Map(TypeHint):
  """
  Represents a mapping type. The *impl_hint* must be one of #typing.Map, #typing.MutableMap or
  #typing.Dict (defaults to #typing.Dict).
  """

  key_type: TypeHint
  value_type: TypeHint
  impl_hint: _GenericAlias = t.Dict

  def to_typing(self) -> t.Any:
    return self.impl_hint[self.key_type.to_typing(), self.value_type.to_typing()]


@dataclass
class Datamodel(TypeHint):
  """
  Represents a type hint for a datamodel (or #Schema). Instances of this type hint are usually
  constructed in a later stage after #from_typing() when a #Concrete type hint was encountered
  that can be interpreted as a #Datamodel.
  """

  schema: 'Schema'


def _unpack_type_hint(hint: t.Any) -> t.Tuple[t.Optional[t.Any], t.List[t.Any]]:
  """
  Unpacks a type hint into it's origin type and parameters.
  """

  if hasattr(t, '_AnnotatedAlias') and isinstance(hint, t._AnnotatedAlias):  # type: ignore
    return t.Annotated, list((hint.__origin__,) + hint.__metadata__)  # type: ignore

  if hasattr(t, '_SpecialGenericAlias') and isinstance(hint, t._SpecialGenericAlias):  # type: ignore
    return hint.__origin__, []

  if isinstance(hint, t._GenericAlias):  # type: ignore
    return hint.__origin__, list(hint.__args__)

  if isinstance(hint, type):
    return hint, []

  if isinstance(hint, t._SpecialForm):
    return hint, []

  return None, []


def _unpack_annotations(hint: TypeHint) -> t.Tuple[TypeHint, t.List[t.Any]]:

  args: t.List[t.Any]

  if isinstance(hint, Annotated):
    hint, args = _unpack_annotations(hint.type)
    return hint, args

  elif isinstance(hint, Union):
    types: t.List[TypeHint] = []
    args = []
    for item in hint.types:
      a, b = _unpack_annotations(item)
      types.append(a)
      args.extend(b)
    return Union(tuple(types)), args

  elif isinstance(hint, Optional):
    hint, args = _unpack_annotations(hint.type)
    return Optional(hint), args

  elif isinstance(hint, Collection):
    hint, args = _unpack_annotations(hint.item_type)
    return type(hint)(hint), args   # type: ignore

  # NOTE(NiklasRosenstein): We explicitly do not unpack the annotations for map keys and values.
  return hint, []


_ORIGIN_CONVERSION = {
  list: t.List,
  set: t.Set,
  dict: t.Dict,
  _Mapping: t.Mapping,
  _MutableMapping: t.MutableMapping,
}


def from_typing(type_hint: t.Any) -> TypeHint:
  """
  Convert a #typing type hint to an API #TypeHint.
  """

  generic, args = _unpack_type_hint(type_hint)
  if generic is not None:
    generic = _ORIGIN_CONVERSION.get(generic, generic)
    if generic == t.List:
      return List(from_typing(args[0]))
    elif generic == t.Set:
      return Set(from_typing(args[0]))
    elif generic in (t.Dict, t.Mapping, t.MutableMapping):
      return Map(from_typing(args[0]), from_typing(args[1]), generic)
    elif generic == t.Optional or (generic == t.Union and None in args and len(args) == 2):  # type: ignore
      if len(args) == 1:
        return Optional(from_typing(args[0]))
      elif len(args) == 2:
        return Optional(from_typing(next(x for x in args if x is not None)))
      else:
        raise ValueError(f'unexpected args for {generic}: {args}')
    elif generic == t.Union:
      if None in args:
        return Optional(from_typing(t.Union[tuple(x for x in args if x is not None)]))
      else:
        return Union(tuple(from_typing(a) for a in args))
    elif hasattr(t, 'Annotated') and generic == t.Annotated:  # type: ignore
      inner_type, args = from_typing(args[0]), args[1:]
      inner_type, inner_args = _unpack_annotations(inner_type)
      return Annotated(inner_type, tuple(inner_args + args))

  if isinstance(type_hint, type):
    return Concrete(type_hint)

  raise ValueError(f'unsupported type hint {type_hint!r}')
