
import uuid

import pytest

from databind.core import ConversionError
from databind.json import mapper


def test_pathlib_converter():
  u = uuid.uuid4()
  assert mapper().serialize(u, uuid.UUID) == str(u)
  assert mapper().deserialize(str(u), uuid.UUID) == u

  with pytest.raises(ConversionError) as excinfo:
    mapper().deserialize('foobar!', uuid.UUID)
  assert str(excinfo.value) == '[None] ($ ConcreteType(uuid.UUID)): badly formed hexadecimal UUID string'
