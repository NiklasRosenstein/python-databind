
"""
Represent supported types for de-/serialization as Python objects.

Type hints from the #typing or #typing_extensions modules can be converted into this format via
the #databind.core.types.converter module.
"""

import abc
import dataclasses
import typing as t

from databind.core.types.utils import type_repr


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
  types may be reinterpreted by #TypeHintAdapter#s (for example the #DataclassAdapter).
  """

  type: t.Type
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

  def __repr__(self) -> str:
    return f'ConcreteType({type_repr(self.type)})'

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
  impl_hint: t.Any = t.Dict
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

  def __repr__(self) -> str:
    return f'MapType({self.key_type!r}, {self.value_type!r})'

  def to_typing(self) -> t.Any:
    return self.impl_hint[self.key_type.to_typing(), self.value_type.to_typing()]

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(MapType(self.key_type.visit(func), self.value_type.visit(func), self.impl_hint, self.annotations))


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
