
import typing as t
import dataclasses
from databind.core.mapper.converter import Context, Direction
from databind.core.types.types import ConcreteType, OptionalType
from databind.core.types.schema import Field, ObjectType, Schema
from databind.json.annotations import with_custom_json_converter
from databind.json import load, mapper


@dataclasses.dataclass
@with_custom_json_converter()
class FieldConfig:
  type: str
  docs: str | None

  @classmethod
  def _convert_json(cls, ctx: 'Context') -> t.Any:
    if ctx.direction.is_deserialize() and isinstance(ctx.value, str):
      return cls(ctx.value, None)
    return NotImplemented


def test_with_custom_json_converter_on_dataclass():
  assert load('foobar', FieldConfig) == FieldConfig('foobar', None)
  assert load({'type': 'foobar', 'docs': None}, FieldConfig) == FieldConfig('foobar', None)
