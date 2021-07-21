
import typing as t
from .location import Format, Location, Position
from .types import from_typing


def test_location_str():
  l1 = Location(None, from_typing(t.Dict[str, t.List[int]]), None, '<string>', Position(0, 0))
  l2 = Location(l1, from_typing(t.List[int]), 'config', None, Position(1, 4))
  l3 = Location(l2, from_typing(int), None, 'https://example.org/config.json', Position(0, 0))

  assert str(l1) == '[<string>:0:0] ($ MapType(ConcreteType(str), ListType(ConcreteType(int))))'
  assert str(l2) == str(l1) + ' -> (.config ListType(ConcreteType(int)))'
  assert str(l3) == str(l2) + ' -> [https://example.org/config.json:0:0] ($ ConcreteType(int))'

  fmt = Format.NO_TYPE
  assert str(l1.format(fmt)) == '[<string>:0:0] $'
  assert str(l2.format(fmt)) == l1.format(fmt) + ' -> .config'
  assert str(l3.format(fmt)) == l2.format(fmt) + ' -> [https://example.org/config.json:0:0] $'

  # Not collapsible because l3 is in a different file.
  assert str(l3.format(fmt | Format.COLLAPSE)) == l2.format(fmt) + ' -> [https://example.org/config.json:0:0] $'

  fmt = Format.NO_FILENAME | Format.NO_TYPE
  assert str(l1.format(fmt)) == '$'
  assert str(l2.format(fmt)) == l1.format(fmt) + ' -> .config'
  assert str(l3.format(fmt)) == l2.format(fmt) + ' -> $'

  # Collapsible now because we don't show filenames.
  assert str(l3.format(fmt | Format.COLLAPSE)) == l2.format(fmt)

  fmt = Format.NO_FILENAME | Format.NO_TYPE | Format.COLLAPSE
  assert str(l1.format(fmt)) == '$'
  assert str(l2.format(fmt)) == l1.format(fmt) + ' -> .config'
  assert str(l3.format(fmt)) == l2.format(fmt)

  fmt = Format.NO_FILENAME | Format.NO_TYPE | Format.COMPACT
  assert str(l1.format(fmt)) == '$'
  assert str(l2.format(fmt)) == l1.format(fmt) + '.config'
  assert str(l3.format(fmt)) == l2.format(fmt) + '$'
  assert str(l3.format(Format.PLAIN)) == l2.format(fmt)
