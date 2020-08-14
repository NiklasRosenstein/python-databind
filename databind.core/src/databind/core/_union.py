
import abc
import dataclasses
from typing import Dict, List, Type, Union
from ._typing import type_repr

__all__ = [
  'UnionTypeError',
  'UnionResolver',
]


class UnionTypeError(TypeError):
  pass


class UnionResolver(metaclass=abc.ABCMeta):
  """
  Abstract base class for union type resolvers.
  """

  @abc.abstractmethod
  def type_for_name(self, type_name: str) -> Type:
    """
    Returns the type for the specified *type_name*. Raise #UnionTypeError if the type name
    cannot be resolved.
    """

  @abc.abstractmethod
  def name_for_type(self, type: Type) -> str:
    """
    Returns the name for the specified *type* (which could be used to retrieve the same type
    with #type_for_name()). Raise #UnionTypeError if the type cannot be named.
    """

  @abc.abstractmethod
  def members(self) -> List[str]:
    """
    Enumerate the union members by name. Implementations may raise a #NotImplementedError.
    """


class StaticUnionResolver(UnionResolver):
  """
  Wraps a dictionary for resolving union members.
  """

  def __init__(self, mapping: Dict[str, Type]) -> None:
    self._mapping = dict(mapping)

  def __getitem__(self, type_name: str) -> Type:
    return self._mapping[type_name]

  def __setitem__(self, type_name: str, type_: Type) -> None:
    self._mapping[type_name] = type_

  def __delitem__(self, type_name: str) -> None:
    del self._mapping[type_name]

  def __eq__(self, other):
    if not isinstance(other, StaticUnionResolver):
      return False
    return self._mapping == other._mapping

  def __ne__(self, other):
    if not isinstance(other, StaticUnionResolver):
      return True
    return self._mapping != other._mapping

  def type_for_name(self, type_name: str) -> Type:
    try:
      return self._mapping[type_name]
    except KeyError:
      raise UnionTypeError(f'type name {type_name!r} could not be resolved')

  def name_for_type(self, type_: Type) -> str:
    for key, value in self._mapping.items():
      if type_ is value:
        return key
      # Check for Optional[type_]
      if (getattr(value, '__origin__', None) == Union and len(value.__args__) == 2 and
          value.__args__[1] == type(None) and type_ == value.__args__[0]):
        return key
    raise UnionTypeError(f'type {type_repr(type_)} could not be resolved')

  def members(self) -> List[str]:
    return list(self._mapping.keys())
