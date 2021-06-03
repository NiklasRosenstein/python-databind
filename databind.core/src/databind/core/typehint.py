
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
import typing_extensions as te
from collections.abc import Mapping as _Mapping, MutableMapping as _MutableMapping
from dataclasses import dataclass
from typing import _type_repr, _GenericAlias

from nr import preconditions  # type: ignore

if t.TYPE_CHECKING:
  from .schema import Schema


class TypeHint(metaclass=abc.ABCMeta):
  """ Base class for an API representation of #typing type hints. """

  def __init__(self) -> None:
    raise TypeError('TypeHint cannot be constructed')

  def __str__(self) -> str:
    return f'>> {_type_repr(self.to_typing())} <<'

  @abc.abstractmethod
  def to_typing(self) -> t.Any:
    """ Convert the type hint back to a #typing representation. """

  @abc.abstractmethod
  def visit(self, func: t.Callable[['TypeHint'], 'TypeHint']) -> 'TypeHint': ...

  def normalize(self) -> 'TypeHint':
    """
    Bubbles up all annotations from nested #Annotated hints into a single #Annotated hint at
    the root if there exists at least one annotation in the tree.
    """

    annotations: t.List[t.Any] = []
    def visitor(hint: TypeHint) -> TypeHint:
      if isinstance(hint, Annotated):
        annotations.extend(hint.annotations)
        return hint.type
      return hint
    new_hint = self.visit(visitor)
    if annotations:
      return Annotated(new_hint, tuple(annotations))
    return new_hint


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

  def visit(self, func: t.Callable[['TypeHint'], 'TypeHint']) -> 'TypeHint':
    return func(self)


@dataclass
class Annotated(TypeHint):
  """ Represents an annotated type. Nested annotations are usually flattened. """

  type: TypeHint
  annotations: t.Tuple[t.Any, ...]

  def __init__(self, type: TypeHint, annotations: t.Sequence[t.Any]) -> None:
    preconditions.check_instance_of(type, TypeHint)
    self.type = type
    self.annotations = tuple(annotations)

  def to_typing(self) -> t.Any:
    return te.Annotated[(self.type.to_typing(),) + self.annotations]  # type: ignore

  def visit(self, func: t.Callable[['TypeHint'], 'TypeHint']) -> 'TypeHint':
    return func(Annotated(self.type.visit(func), self.annotations))


@dataclass
class Union(TypeHint):
  """ Represents a union of types. Unions never represent optionals, as is the case in typing. """

  types: t.Tuple[TypeHint, ...]

  def to_typing(self) -> t.Any:
    return t.Union[self.types]

  def visit(self, func: t.Callable[['TypeHint'], 'TypeHint']) -> 'TypeHint':
    return func(Union(tuple(t.visit(func) for t in self.types)))


@dataclass
class Optional(TypeHint):
  """ Represents an optional type. """

  type: TypeHint

  def to_typing(self) -> t.Any:
    return t.Optional[self.type]

  def visit(self, func: t.Callable[['TypeHint'], 'TypeHint']) -> 'TypeHint':
    return func(Optional(self.type.visit(func)))


class Collection(TypeHint):
  """ Represents a collection type. This is still abstract. """

  item_type: TypeHint

  def visit(self, func: t.Callable[['TypeHint'], 'TypeHint']) -> 'TypeHint':
    return func(type(self)(self.item_type.visit(func)))


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

  def visit(self, func: t.Callable[['TypeHint'], 'TypeHint']) -> 'TypeHint':
    return func(Map(self.key_type.visit(func), self.value_type.visit(func)))


@dataclass
class Datamodel(TypeHint):
  """
  Represents a type hint for a datamodel (or #Schema). Instances of this type hint are usually
  constructed in a later stage after #from_typing() when a #Concrete type hint was encountered
  that can be interpreted as a #Datamodel.
  """

  schema: 'Schema'

  def to_typing(self) -> t.Any:
    return self.schema.python_type

  def visit(self, func: t.Callable[['TypeHint'], 'TypeHint']) -> 'TypeHint':
    return func(self)


def _unpack_type_hint(hint: t.Any) -> t.Tuple[t.Optional[t.Any], t.List[t.Any]]:
  """
  Unpacks a type hint into it's origin type and parameters.
  """

  if hasattr(te, '_AnnotatedAlias') and isinstance(hint, te._AnnotatedAlias):  # type: ignore
    return te.Annotated, list((hint.__origin__,) + hint.__metadata__)  # type: ignore

  if hasattr(t, '_SpecialGenericAlias') and isinstance(hint, t._SpecialGenericAlias):  # type: ignore
    return hint.__origin__, []

  if isinstance(hint, t._GenericAlias):  # type: ignore
    return hint.__origin__, list(hint.__args__)

  if isinstance(hint, type):
    return hint, []

  if isinstance(hint, t._SpecialForm):
    return hint, []

  return None, []


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
      if len(args) == 1:
        return from_typing(args[0])
      elif type(None) in args:
        return Optional(from_typing(t.Union[tuple(x for x in args if x is not type(None))]))
      else:
        return Union(tuple(from_typing(a) for a in args))
    elif hasattr(te, 'Annotated') and generic == te.Annotated:  # type: ignore
      return Annotated(from_typing(args[0]), args[1:])

  if isinstance(type_hint, type):
    return Concrete(type_hint)

  raise ValueError(f'unsupported type hint {type_hint!r}')
