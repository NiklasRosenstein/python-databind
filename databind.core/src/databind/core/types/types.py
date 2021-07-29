
"""
This module represents a subset of the #typing type hints as a stable API. The concepts exposed by
the #typing module are represented as instances of the #TypeHint subclass (e.g., #Union, #List,
#Map). The purpose of this module is to provide an easy method to introspect type hints.

Use #from_typing() to convert an actual type hint to the stable API and #TypeHint.to_typing() for
the reverse operation.
"""

import abc
import dataclasses
import typing as t
import typing_extensions as te
from typing import _type_repr, _GenericAlias  # type: ignore


if t.TYPE_CHECKING:
  from .schema import Schema
  from .union import IUnionSubtypes, UnionStyle


class BaseType(metaclass=abc.ABCMeta):
  """ Base class for an API representation of #typing type hints. """

  annotations: t.List[t.Any]

  def __init__(self) -> None:
    raise TypeError('TypeHint cannot be constructed')

  @abc.abstractmethod
  def to_typing(self) -> t.Any:
    """ Convert the type hint back to a #typing representation. """

  @abc.abstractmethod
  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType': ...


@dataclasses.dataclass
class ConcreteType(BaseType):
  """
  Represents a concrete type, that is an actual Python type, not a typing hint. Note that concrete
  types may be reinterpreted as a #Datamodel by the object mapper, but #from_typing() cannot do
  that because the reinterpretation is up to the object mapper configuration.
  """

  type: t.Type
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

  def __repr__(self) -> str:
    return f'ConcreteType({self.type.__name__})'

  def to_typing(self) -> t.Any:
    return self.type

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(self)


@dataclasses.dataclass
class ImplicitUnionType(BaseType):
  """
  Represents an implicit union of types (i.e. accept as input and output values of multiple
  types and use the first match. Implicit unions never represent optional values, as is the
  case with #typing.Union (i.e. you can have `t.Union[int, str, None]` but it must be represented
  as `OptionalType(ImplicitUnionType([int, str])))`).
  """

  types: t.Tuple[BaseType, ...]
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

  def __repr__(self) -> str:
    return f'ImplicitUnionType({", ".join(map(repr, self.types))})'

  def to_typing(self) -> t.Any:
    return t.Union[tuple(x.to_typing() for x in self.types)]

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(ImplicitUnionType(tuple(t.visit(func) for t in self.types), self.annotations))


@dataclasses.dataclass
class OptionalType(BaseType):
  """ Represents an optional type. """

  type: BaseType
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

  def __repr__(self) -> str:
    return f'OptionalType({self.type!r})'

  def to_typing(self) -> t.Any:
    return t.Optional[self.type]

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(OptionalType(self.type.visit(func), self.annotations))


class CollectionType(BaseType):
  """ Represents a collection type. This is still abstract. """

  item_type: BaseType
  python_type: t.Type[t.Collection]
  annotations: t.List[t.Any]

  def __repr__(self) -> str:
    result = f'{type(self).__name__}({self.item_type!r}'
    if self.python_type != type(self).python_type:
      result += ', python_type=' + self.python_type.__name__
    return result + ')'

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(type(self)(self.item_type.visit(func), self.python_type, self.annotations))  # type: ignore


@dataclasses.dataclass(repr=False)
class ListType(CollectionType):
  """ Represents a list type. """

  item_type: BaseType
  python_type: t.Type[t.Collection] = list
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

  def to_typing(self) -> t.Any:
    return t.List[self.item_type.to_typing()]  # type: ignore


@dataclasses.dataclass(repr=False)
class SetType(CollectionType):
  """ Represents a set type. """

  item_type: BaseType
  python_type: t.Type[t.Collection] = set
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

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
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

  def __repr__(self) -> str:
    return f'MapType({self.key_type!r}, {self.value_type!r})'

  def to_typing(self) -> t.Any:
    return self.impl_hint[self.key_type.to_typing(), self.value_type.to_typing()]

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(MapType(self.key_type.visit(func), self.value_type.visit(func), self.impl_hint, self.annotations))


@dataclasses.dataclass
class ObjectType(BaseType):
  """
  Represents a type hint for a datamodel (or #Schema). Instances of this type hint are usually
  constructed in a later stage after #from_typing() when a #Concrete type hint was encountered
  that can be interpreted as an #ObjectType (see #databind.core.default.dataclass.DataclassModule).
  """

  schema: 'Schema'
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

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
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

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


from .union import UnionStyle
UnionType.DEFAULT_STYLE = UnionStyle.nested
