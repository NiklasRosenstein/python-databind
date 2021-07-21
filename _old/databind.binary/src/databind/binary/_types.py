
from typing import TYPE_CHECKING, Optional, Type, Union
from databind.core import FieldMetadata, type_repr

__all__ = [
  'u8','i8',
  'u16', 'i16',
  'u32', 'i32',
  'u64', 'i64',
  'pointer',
  'cstr',
]


if TYPE_CHECKING:
  from typing import Protocol
  class FormattableType(Protocol):
    fmt: str


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

class cstr(str):
  pass


all_plain_types = [globals()[k] for k in __all__]


def get_format_for_type(
  type_: 'Union[Type[FormattableType], bool, Type[cstr]]',
  field_metadata: Optional[FieldMetadata],
) -> str:
  if isinstance(type_, type) and issubclass(type_, int) and hasattr(type_, 'fmt'):
    return type_.fmt
  elif type_ == bool:
    return '?'
  elif type_ == cstr:
    if not field_metadata or not 'size' in field_metadata.metadata:
      raise TypeError(f'type "cstr" must have metadata field "size"')
    size: int = field_metadata.metadata['size']
    return f'{size}s'
  else:
    raise TypeError(f'unable to get struct format specifier for {type_repr(type_)}')
