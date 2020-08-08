
import struct
from databind.core import datamodel
from databind.binary import *

@datamodel
class A:
  a: i8
  b: i32
  c: cstring(10)


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
