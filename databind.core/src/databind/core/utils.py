
from typing import Callable, Iterable, Optional, TypeVar

T = TypeVar('T')


def find(predicate: Callable[[Optional[T]], bool], it: Iterable[T]) -> Optional[T]:
  return next(filter(predicate, it), None)
