

import enum
from typing import Any


class Dumper:

  def dump(self, value: Any, root: bool = False) -> str:
    def _wrap(r: str) -> str:
      if not root:
        return '{' + r + '}'
      return r
    if isinstance(value, dict):
      if 'type' in value and value['type'] in value and len(value) == 2:
        return value['type'] + self.dump(value[value['type']])
      return _wrap(','.join(f'{k}={self.dump(v)}' for k, v in value.items()))
    elif isinstance(value, list):
      return _wrap(','.join(map(self.dump, value)))
    elif isinstance(value, (int, float, str)):
      return str(value)
    else:
      raise TypeError(f'cannot dump value of type {type(value).__name__}')


def dumps(value: Any) -> str:
  return Dumper().dump(value, True)
