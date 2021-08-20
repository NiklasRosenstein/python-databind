
import uuid

from databind.json import mapper


def test_pathlib_converter():
  u = uuid.uuid4()
  assert mapper().serialize(u, uuid.UUID) == str(u)
  assert mapper().deserialize(str(u), uuid.UUID) == u
