
import typing as t
from .location import Location
from .typehint import from_typing


def test_location_str():
  l1 = Location(from_typing(t.Dict[str, t.List[int]]), '<string>', Location.Position(0, 0))
  l2 = Location(from_typing(t.List[int]), None, Location.Position(1, 4), l1, 'config')
  l3 = Location(from_typing(int), 'https://example.org/config.json', Location.Position(0, 0), l2)

  assert str(l1) == '[<string>:0:0] ($ typing.Dict[str, typing.List[int]])'
  assert str(l2) == str(l1) + ' -> (.config typing.List[int])'
  assert str(l3) == str(l2) + ' -> [https://example.org/config.json:0:0] ($ int)'
