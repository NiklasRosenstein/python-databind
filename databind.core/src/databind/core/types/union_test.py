
from databind.core.types import ConcreteType
from .union import ImportSubtypes
from . import root


class Foobar: pass


def test_import_subtypes():
  assert ImportSubtypes().get_type_name(Foobar, root) == f'{__name__}.Foobar'
  assert ImportSubtypes().get_type_by_name(f'{__name__}.Foobar', root) == ConcreteType(Foobar)
