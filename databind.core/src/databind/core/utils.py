
from typing import Callable, Iterable, Optional, T


def find(predicate: Callable[[T], bool], it: Iterable[T]) -> Optional[T]:
  return next(filter(predicate, it), None)
