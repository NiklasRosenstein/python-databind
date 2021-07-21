
import pytest
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
