
import typing as t
from .location import Location, Position
from .types import from_typing


def test_location_str():
  l1 = Location(None, from_typing(t.Dict[str, t.List[int]]), None, '<string>', Position(0, 0))
  l2 = Location(l1, from_typing(t.List[int]), 'config', None, Position(1, 4))
  l3 = Location(l2, from_typing(int), None, 'https://example.org/config.json', Position(0, 0))

  assert str(l1) == '[<string>:0:0] ($ MapType(key_type=ConcreteType(type=str))>> typing.Dict[str, typing.List[int]] <<)'
  assert str(l2) == str(l1) + ' -> (.config >> typing.List[int] <<)'
  assert str(l3) == str(l2) + ' -> [https://example.org/config.json:0:0] ($ >> int <<)'
