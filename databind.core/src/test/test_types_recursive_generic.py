
import dataclasses
import typing as t

T = t.TypeVar('T')


@dataclasses.dataclass
class A(t.Generic[T]):
  values: t.List[T]

class B(A[A]):
  pass

class C(A[B]):
  pass


def test_recursive_generic():
  from databind.json import load
  assert load(
    {'values': [{'values': [{'values': [{'values': [{'values': []}]}]}]}]},
    C
  ) == C([B([A([A([A([])])])])])
