
import dataclasses
import typing as t
import typing_extensions as te
import pytest
from databind.core.annotations import fieldinfo
from databind.core.objectmapper import ObjectMapper
from databind.core.schema import SchemaDefinitionError
from databind.core.types import ObjectType, from_typing

@pytest.fixture
def mapper() -> ObjectMapper:
  return ObjectMapper.default()


def test_schema_flat_fields_check(mapper: ObjectMapper):

  @dataclasses.dataclass
  class A:
    foo: str
    bar: str

  assert isinstance(mapper.adapt_type_hint(from_typing(A)), ObjectType)

  @dataclasses.dataclass
  class B:
    foo: str
    a: te.Annotated[A, fieldinfo(flat=True)]  # Field cannot be flat because of conflicting members "foo".

  with pytest.raises(SchemaDefinitionError) as excinfo:
    assert isinstance(mapper.adapt_type_hint(from_typing(B)), ObjectType)
  assert '($.foo, $.a.foo)' in str(excinfo)
