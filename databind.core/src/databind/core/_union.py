
import abc
import dataclasses
from typing import Dict, List, Optional, Type, Union, get_type_hints
from .utils import type_repr

__all__ = [
  'UnionResolver',
  'UnionTypeError',
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


class _MappingUnionResolverMixin(UnionResolver):
  """
  Wraps a dictionary for resolving union members.
  """

  _mapping: Dict[str, Type]

  def __getitem__(self, type_name: str) -> Type:
    return self._mapping[type_name]

  def __setitem__(self, type_name: str, type_: Type) -> None:
    self._mapping[type_name] = type_

  def __delitem__(self, type_name: str) -> None:
    del self._mapping[type_name]

  def __eq__(self, other):
    if not isinstance(other, _MappingUnionResolverMixin):
      return False
    return self._mapping == other._mapping

  def __ne__(self, other):
    if not isinstance(other, _MappingUnionResolverMixin):
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


class StaticUnionResolver(_MappingUnionResolverMixin):

  def __init__(self, mapping: Dict[str, Type]) -> None:
    self._mapping = dict(mapping)


class ClassUnionResolver(_MappingUnionResolverMixin):

  def __init__(self, cls: Type) -> None:
    self._cls = cls

  @property
  def _mapping(self) -> Dict[str, Type]:  # type: ignore
    return get_type_hints(self._cls)


class InterfaceUnionResolver(_MappingUnionResolverMixin):

  def __init__(self, mapping: Optional[Dict[str, Type]] = None) -> None:
    self._mapping = mapping or {}

  def register_implementation(self, name: str, impl: Type) -> None:
    assert isinstance(impl, type), 'implementations must be types'
    if name in self._mapping:
      raise ValueError(f'an implementation with name {name!r} is already defined')
    self._mapping[name] = impl
