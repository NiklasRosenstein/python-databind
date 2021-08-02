
import typing as t
from databind.core.mapper.location import Format, Location, Position
from databind.core.mapper import ObjectMapper


def test_location_str():
  mapper = ObjectMapper()

  l1 = Location(None, mapper.adapt_type_hint(t.Dict[str, t.List[int]]), None, '<string>', Position(0, 0))
  l2 = Location(l1, mapper.adapt_type_hint(t.List[int]), 'config', None, Position(1, 4))
  l3 = Location(l2, mapper.adapt_type_hint(int), None, 'https://example.org/config.json', Position(0, 0))

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
