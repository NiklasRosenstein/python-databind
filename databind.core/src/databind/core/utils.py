
from typing import Callable, Iterable, Optional, TypeVar
from typing import Any, Iterator, Optional, MutableMapping, TypeVar, Union, overload
from collections import abc

__all__ = ['find', 'ChainDict']
T = TypeVar('T')
KT = TypeVar('KT')
VT = TypeVar('VT')


def find(predicate: Callable[[Optional[T]], bool], it: Iterable[T]) -> Optional[T]:
  return next(filter(predicate, it), None)


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
