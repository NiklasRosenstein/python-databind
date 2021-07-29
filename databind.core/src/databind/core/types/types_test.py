
from .types import ConcreteType, ListType, SetType


def test_visit():
  assert ConcreteType(int, [42]).visit(lambda x: x) == ConcreteType(int, [42])
  assert ListType(ConcreteType(int, [42]), tuple, ['foo']).visit(lambda x: x) == ListType(ConcreteType(int, [42]), tuple, ['foo'])
  assert SetType(ConcreteType(int, [42]), tuple, ['foo']).visit(lambda x: x) == SetType(ConcreteType(int, [42]), tuple, ['foo'])
