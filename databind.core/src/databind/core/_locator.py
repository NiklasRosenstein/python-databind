
import string
from typing import Any, Dict, List, Sequence, Union


class Locator:
  """
  A locator represents the path of an object in a nested data structure as a list of string and
  integer indices. Locator objects are immutable.
  """

  _WHITELISTED_KEY_CHARACTERS = string.ascii_letters + string.digits + '_-'

  def __init__(self, items: Sequence[Union[str, int]]) -> None:
    self._items = items

  __iter__ = lambda self: iter(self._items)
  __len__ = lambda self: len(self._items)
  __getitem__ = lambda self, index: self._items[index]
  __repr__ = lambda self: 'Locator({})'.format(str(self))
  __bool__ = lambda self: bool(self._items)
  __nonzero__ = __bool__

  def __str__(self):
    parts = ['$']
    for item in self._items:
      if isinstance(item, int):
        parts.append('[' + str(item) + ']')
      else:
        item = str(item)
        if '"' in item:
          item = item.replace('"', '\\"')
        if any(c not in self._WHITELISTED_KEY_CHARACTERS for c in item):
          item = '"' + item + '"'
        parts.append('.' + item)
    return ''.join(parts)

  def resolve(self, root: Union[Any, Dict, List]) -> Any:
    """
    Accesses the value represented by this Locator object starting from *root*.

    >>> root = {'values': [1, 2, 3]}
    >>> Locator(['values', 1]).access(root)
    2

    :param root: The object to start indexing from.
    :raises KeyError: If an item in an object cannot be accessed.
    :raises IndexError: If an item in a list cannot be accessed.
    ``` """

    value = root
    for item in self._items:
      try:
        value = value[item]  # type: ignore
      except KeyError as exc:
        raise KeyError(str(self))
      except IndexError as exc:
        raise IndexError('{} at {}'.format(exc, self))

    return value

  def push(self, item: Union[str, int]) -> 'Locator':
    """
    Create a copy of this locator with *item* appended to it.
    """

    items = list(self._items)
    items.append(item)
    return Locator(items)

  def pop(self) -> 'Locator':
    """
    Creates a copy of this locator, with the last element removed.
    """

    items = list(self._items)
    items.pop()
    return Locator(items)
