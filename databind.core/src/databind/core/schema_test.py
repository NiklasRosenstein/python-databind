
import dataclasses
import typing_extensions as te
import pytest
from databind.core.annotations import fieldinfo
from databind.core.objectmapper import ObjectMapper
from databind.core.schema import SchemaDefinitionError
from databind.core.types import ObjectType, from_typing


def test_schema_flat_fields_check():

  @dataclasses.dataclass
  class A:
    foo: str
    bar: str

  @dataclasses.dataclass
  class B:
    foo: str
    a: te.Annotated[A, fieldinfo(flat=True)]  # Field cannot be flat because of conflicting members "foo".

  mapper = ObjectMapper.default()
  assert isinstance(mapper.adapt_type_hint(from_typing(A)), ObjectType)

  with pytest.raises(SchemaDefinitionError) as excinfo:
    assert isinstance(mapper.adapt_type_hint(from_typing(B)), ObjectType)
  assert '($.foo, $.a.foo)' in str(excinfo)
