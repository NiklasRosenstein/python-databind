
from databind.core.annotations.unionclass import unionclass
from databind.core.types import ConcreteType
from .union import ImportSubtypes


class Foobar: pass


def test_import_subtypes():
  assert ImportSubtypes().get_type_name(Foobar) == f'{__name__}.Foobar'
  assert ImportSubtypes().get_type_by_name(f'{__name__}.Foobar') == ConcreteType(Foobar)
  assert ImportSubtypes().get_type_by_name(f'databind.core.annotations.unionclass.unionclass') == ConcreteType(unionclass)
