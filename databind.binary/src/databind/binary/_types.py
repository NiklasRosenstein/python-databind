
from typing import Type
from databind.core import type_repr

__all__ = [
  'u8','i8',
  'u16', 'i16',
  'u32', 'i32',
  'u64', 'i64',
  'pointer',
  'cstring',
]


class i8(int):
  fmt = 'b'


class u8(int):
  fmt = 'B'


class i16(int):
  fmt = 'h'


class u16(int):
  fmt = 'H'


class i32(int):
  fmt = 'i'


class u32(int):
  fmt = 'I'


class i64(int):
  fmt = 'l'


class u64(int):
  fmt = 'L'


class pointer(int):
  fmt = 'P'


class cstring:

  def __init__(self, size: int) -> None:
    self.size = size
    self.__origin__ = cstring


all_plain_types = [globals()[k] for k in __all__]


def get_format_for_type(type_: Type) -> str:
  if isinstance(type_, type) and issubclass(type_, int) and hasattr(type_, 'fmt'):
    return type_.fmt
  elif type_ == bool:
    return '?'
  elif type_ == cstring:
    raise TypeError(f'"cstring" must be instantiated to supply size information')
  elif isinstance(type_, cstring):
    return f'{type_.size}s'
  else:
    raise TypeError(f'unable to get struct format specifier for {type_repr(type_)}')
