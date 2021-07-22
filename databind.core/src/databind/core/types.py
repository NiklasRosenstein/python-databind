
"""
This module represents a subset of the #typing type hints as a stable API. The concepts exposed by
the #typing module are represented as instances of the #TypeHint subclass (e.g., #Union, #List,
#Map). The purpose of this module is to provide an easy method to introspect type hints.

Use #from_typing() to convert an actual type hint to the stable API and #TypeHint.to_typing() for
the reverse operation.
"""

__all__ = [
  'BaseType',
  'ConcreteType',
  'AnnotatedType',
  'ImplicitUnionType',
  'OptionalType',
  'CollectionType',
  'ListType',
  'SetType',
  'MapType',
  'ObjectType',
  'UnionType',
  'from_typing',
]

import abc
import dataclasses
import sys
import typing as t
import typing_extensions as te
from collections.abc import Mapping as _Mapping, MutableMapping as _MutableMapping
from typing import _type_repr, _GenericAlias  # type: ignore

from nr import preconditions


if t.TYPE_CHECKING:
  from databind.core.union import IUnionSubtypes, UnionStyle
  from .schema import Schema


class BaseType(metaclass=abc.ABCMeta):
  """ Base class for an API representation of #typing type hints. """

  def __init__(self) -> None:
    raise TypeError('TypeHint cannot be constructed')

  @abc.abstractmethod
  def to_typing(self) -> t.Any:
    """ Convert the type hint back to a #typing representation. """

  @abc.abstractmethod
  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType': ...

  def normalize(self) -> 'BaseType':
    """
    Bubbles up all annotations from nested #Annotated hints into a single #Annotated hint at
    the root if there exists at least one annotation in the tree.
    """

    annotations: t.List[t.Any] = []
    def visitor(hint: BaseType) -> BaseType:
      if isinstance(hint, AnnotatedType):
        annotations.extend(hint.annotations)
        return hint.type
      return hint
    new_hint = self.visit(visitor)
    if annotations:
      return AnnotatedType(new_hint, tuple(annotations))
    return new_hint


@dataclasses.dataclass
class ConcreteType(BaseType):
  """
  Represents a concrete type, that is an actual Python type, not a typing hint. Note that concrete
  types may be reinterpreted as a #Datamodel by the object mapper, but #from_typing() cannot do
  that because the reinterpretation is up to the object mapper configuration.
  """

  type: t.Type

  def __repr__(self) -> str:
    return f'ConcreteType({self.type.__name__})'

  def to_typing(self) -> t.Any:
    return self.type

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(self)


@dataclasses.dataclass
class AnnotatedType(BaseType):
  """ Represents an annotated type. Nested annotations are flattened with #normalize(). """

  type: BaseType
  annotations: t.Tuple[t.Any, ...]

  def __init__(self, type_: BaseType, annotations: t.Sequence[t.Any]) -> None:
    preconditions.check_instance_of(type_, BaseType)  # type: ignore
    self.type = type_
    self.annotations = tuple(annotations)

  def __repr__(self) -> str:
    return f'AnnotatedType({self.type!r}, annotations={self.annotations!r})'

  def to_typing(self) -> t.Any:
    return te.Annotated[(self.type.to_typing(),) + self.annotations]  # type: ignore

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(AnnotatedType(self.type.visit(func), self.annotations))

  @staticmethod
  def unpack(type_: 'BaseType') -> t.Tuple[BaseType, t.Tuple[t.Any, ...]]:
    if isinstance(type_, AnnotatedType):
      return type_.type, type_.annotations
    return type_, ()


@dataclasses.dataclass
class ImplicitUnionType(BaseType):
  """
  Represents an implicit union of types (i.e. accept as input and output values of multiple
  types and use the first match. Implicit unions never represent optional values, as is the
  case with #typing.Union (i.e. you can have `t.Union[int, str, None]` but it must be represented
  as `OptionalType(ImplicitUnionType([int, str])))`).
  """

  types: t.Tuple[BaseType, ...]

  def __repr__(self) -> str:
    return f'ImplicitUnionType({", ".join(map(repr, self.types))})'

  def to_typing(self) -> t.Any:
    return t.Union[tuple(x.to_typing() for x in self.types)]

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(ImplicitUnionType(tuple(t.visit(func) for t in self.types)))


@dataclasses.dataclass
class OptionalType(BaseType):
  """ Represents an optional type. """

  type: BaseType

  def __repr__(self) -> str:
    return f'OptionalType({self.type!r})'

  def to_typing(self) -> t.Any:
    return t.Optional[self.type]

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(OptionalType(self.type.visit(func)))


class CollectionType(BaseType):
  """ Represents a collection type. This is still abstract. """

  item_type: BaseType
  python_type: t.Type[t.Collection]

  def __repr__(self) -> str:
    result = f'{type(self).__name__}({self.item_type!r}'
    if self.python_type != type(self).python_type:
      result += ', python_type=' + self.python_type.__name__
    return result + ')'

  # https://github.com/python/mypy/issues/5374
  def to_typing(self) -> t.Any:
    raise NotImplementedError

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(type(self)(self.item_type.visit(func), self.python_type))  # type: ignore


@dataclasses.dataclass(repr=False)
class ListType(CollectionType):
  """ Represents a list type. """

  item_type: BaseType
  python_type: t.Type[t.Collection] = list

  def to_typing(self) -> t.Any:
    return t.List[self.item_type.to_typing()]  # type: ignore


@dataclasses.dataclass(repr=False)
class SetType(CollectionType):
  """ Represents a set type. """

  item_type: BaseType
  python_type: t.Type[t.Collection] = set

  def to_typing(self) -> t.Any:
    return t.Set[self.item_type.to_typing()]  # type: ignore


@dataclasses.dataclass
class MapType(BaseType):
  """
  Represents a mapping type. The *impl_hint* must be one of #typing.Map, #typing.MutableMap or
  #typing.Dict (defaults to #typing.Dict).
  """

  key_type: BaseType
  value_type: BaseType
  impl_hint: _GenericAlias = t.Dict

  def __repr__(self) -> str:
    return f'MapType({self.key_type!r}, {self.value_type!r})'

  def to_typing(self) -> t.Any:
    return self.impl_hint[self.key_type.to_typing(), self.value_type.to_typing()]

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(MapType(self.key_type.visit(func), self.value_type.visit(func), self.impl_hint))


@dataclasses.dataclass
class ObjectType(BaseType):
  """
  Represents a type hint for a datamodel (or #Schema). Instances of this type hint are usually
  constructed in a later stage after #from_typing() when a #Concrete type hint was encountered
  that can be interpreted as an #ObjectType (see #databind.core.default.dataclass.DataclassModule).
  """

  schema: 'Schema'

  def __repr__(self) -> str:
    return f'ObjectType({self.schema.python_type.__name__})'

  def to_typing(self) -> t.Any:
    return self.schema.python_type

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(self)


@dataclasses.dataclass
class UnionType(BaseType):
  """
  Represents a union of multiple types that is de-/serialized with a discriminator value.
  """

  DEFAULT_STYLE: t.ClassVar['UnionStyle']
  DEFAULT_DISCRIMINATOR_KEY = 'type'

  subtypes: 'IUnionSubtypes'
  style: t.Optional['UnionStyle'] = None
  discriminator_key: t.Optional[str] = None
  name: t.Optional[str] = None
  python_type: t.Optional[t.Any] = None  # Can be a Python type or an actual type hint

  def __post_init__(self) -> None:
    if not self.name and self.python_type is None:
      raise ValueError(f'UnionType() requires either name or python_type')

  def __repr__(self) -> str:
    return f'UnionType({self.name or _type_repr(self.python_type)})'

  def to_typing(self) -> t.Any:
    return self.python_type

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(self)


class UnknownType(BaseType):
  """
  Can be used to represent an unknown type.
  """

  def __init__(self) -> None:
    pass

  def __repr__(self) -> str:
    return 'UnknownType()'

  def to_typing(self) -> t.Any:
    raise NotImplementedError('UnknownType cannot be converted to typing')

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    raise NotImplementedError('UnknownType cannot be visited')


def _unpack_type_hint(hint: t.Any) -> t.Tuple[t.Optional[t.Any], t.List[t.Any]]:
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

  type_, args = _unpack_type_hint(type_hint)
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


_ORIGIN_CONVERSION = {
  list: t.List,
  set: t.Set,
  dict: t.Dict,
  _Mapping: t.Mapping,
  _MutableMapping: t.MutableMapping,
}


def from_typing(type_hint: t.Any) -> BaseType:
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
      return AnnotatedType(from_typing(args[0]), args[1:])

  if isinstance(type_hint, type):
    return ConcreteType(type_hint)

  raise ValueError(f'unsupported type hint {type_hint!r}')


from .union import UnionStyle
UnionType.DEFAULT_STYLE = UnionStyle.nested
