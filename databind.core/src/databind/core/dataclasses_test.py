
import pytest
import dataclasses
from .dataclasses import *


def test_non_default_argument_after_default():

  @dataclass
  class A:
    a: int
    b: str = 'foo'
    c: float = field(annotations=[42])

  assert A.__dataclass_fields__['b'].metadata == {}
  assert A.__dataclass_fields__['c'].metadata == {'databind.core.annotations': [42]}

  assert A(42, c=1.0) == A(42, 'foo', 1.0)
  assert A(42, c=1.0).c == 1.0

  with pytest.raises(TypeError) as excinfo:
    A(42)
  assert str(excinfo.value) == "missing required argument 'c'"


def test_dataclass_non_default_arguments_subclass():
  @dataclass
  class A:
    a: str = 'aval'
    b: str

  @dataclass
  class B(A):
    c: str
  assert [x.name for x in fields(B)] == ['a', 'b', 'c']
  B('a', 'b', 'c')

  with pytest.raises(TypeError) as excinfo:
    @dataclasses.dataclass
    class C(A):
      c: str
  assert str(excinfo.value) == "non-default argument 'c' follows default argument"
