
import types
from typing import Any, Callable, Iterable, Iterator, Optional, MutableMapping, Tuple, Type, TypeVar, Union, overload
from collections import abc

__all__ = [
  'find',
  'type_repr',
  'ChainDict',
]

T = TypeVar('T')
KT = TypeVar('KT')
VT = TypeVar('VT')


def expect(val: Optional[T]) -> T:
  """
  Asserts that *val* is not #None and returns it.
  """

  assert val is not None, "expected not-None value"
  return val


def find(predicate: Callable[[Optional[T]], bool], it: Iterable[T]) -> Optional[T]:
  return next(filter(predicate, it), None)


def _type_repr(obj: Any) -> str:
  # Borrowed from typing in CPython 3.7
  if isinstance(obj, type):
      if obj.__module__ == 'builtins':
          return obj.__qualname__
      return f'{obj.__module__}.{obj.__qualname__}'
  if obj is ...:
      return('...')
  if isinstance(obj, types.FunctionType):
      return obj.__name__
  return repr(obj)


try:
  from typing import _type_repr as type_repr  # type: ignore
except ImportError:
  type_repr = _type_repr


def find_orig_base(type_: Type, generic_type: Any) -> Optional[Any]:
  """
  Finds an instance of the specified *generic_meta* in the `__orig_bases__` attribute of
  the specified *type_*. This is used to find the parametrized generic in the bases of a
  class.
  """

  bases = getattr(type_, '__orig_bases__', [])

  generic_choices: Tuple[Any, ...] = (generic_type,)
  if generic_type.__origin__:
    generic_choices += (generic_type.__origin__,)

  for base in bases:
    if base == generic_type or getattr(base, '__origin__', None) in generic_choices:
      return base
  for base in bases:
    result = find_orig_base(base, generic_type)
    if result is not None:
      return result
  return None


class ChainDict(MutableMapping[KT, VT]):
  """
  A dictionary that wraps a list of dictionaries. The dictionaries passed
  into the #ChainDict will not be mutated. Setting and deleting values will
  happen on the first dictionary passed.
  """

  def __init__(self, *dicts):
    if not dicts:
      raise ValueError('need at least one argument')
    self._major = dicts[0]
    self._dicts = list(dicts)
    self._deleted = set()
    self._in_repr = False

  def __repr__(self) -> str:
    if self._in_repr:
      return 'ChainDict(...)'
    else:
      self._in_repr = True
      try:
        return 'ChainDict({})'.format(dict(self.items()))
      finally:
        self._in_repr = False

  def __iter__(self) -> Iterator[KT]:
    seen = set()
    for d in self._dicts:
      for key in d.keys():
        if key not in seen and key not in self._deleted:
          yield key
          seen.add(key)

  def __len__(self) -> int:
    return sum(1 for x in self.keys())

  def __contains__(self, key: Any) -> bool:
    if key not in self._deleted:
      for d in self._dicts:
        if key in d:
          return True
    return False

  def __getitem__(self, key: KT) -> VT:
    if key not in self._deleted:
      for d in self._dicts:
        try: return d[key]
        except KeyError: pass
    raise KeyError(key)

  def __setitem__(self, key: KT, value: VT) -> None:
    self._major[key] = value
    self._deleted.discard(key)

  def __delitem__(self, key: KT) -> None:
    if key not in self:
      raise KeyError(key)
    self._major.pop(key, None)
    self._deleted.add(key)

  def clear(self):
    self._major.clear()
    self._deleted.update(self.keys())
