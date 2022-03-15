
import enum
import typing_extensions as te

from databind.core import annotations as A
from databind.json import mapper


class Color(enum.Enum):
  RED = 0
  GREEN = 1
  BLUE: te.Annotated[int, A.alias('ImBlue')] = 2


def test_enum_converter():

  assert mapper().serialize(Color.RED, Color) == 'RED'
  assert mapper().deserialize('RED', Color) == Color.RED

  assert mapper().serialize(Color.BLUE, Color) == 'ImBlue'
  assert mapper().deserialize('ImBlue', Color) == Color.BLUE
  assert mapper().deserialize('BLUE', Color) == Color.BLUE

  m = mapper()
  m.add_field_annotation(Color, 'GREEN', A.alias('greeeeen'))
  assert m.serialize(Color.RED, Color) == 'RED'
  assert m.serialize(Color.GREEN, Color) == 'greeeeen'
  assert m.deserialize('GREEN', Color) == Color.GREEN
  assert m.deserialize('greeeeen', Color) == Color.GREEN
