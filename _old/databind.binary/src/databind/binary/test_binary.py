
import struct
from databind.core import datamodel, field
from databind.binary import to_bytes, from_bytes, i8, i32, cstr


class cstring_type:

  def __init__(self, origin=None, size=None):
    self.origin = origin
    self.size = size

  def __getitem__(self, size: int) -> 'cstring_type':
    return cstring_type(self.origin or self, size)


cstring = cstring_type()


@datamodel
class A:
  a: i8
  b: i32
  c: cstr = field(metadata={'size': 10})


def test_from_bytes():
  assert from_bytes(i32, b'2345') == struct.unpack('i', b'2345')[0]
  assert from_bytes(A, b'10002345FoobarSpam') == A(
    a=49,
    b=struct.unpack('i', b'2345')[0],
    c=b'FoobarSpam'
  )


def test_to_bytes():
  assert to_bytes(i32(123)) == struct.pack('i', 123)
  assert to_bytes(A(1, 123, b'FoobarSpam')) == struct.pack('bi10s', 1, 123, b'FoobarSpam')
