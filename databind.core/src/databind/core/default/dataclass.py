
"""
The #DataclassModule provides the type adaptation for classes decorated with `@dataclass` to be
interpreted as a datamodel.
"""

import typing as t
from dataclasses import is_dataclass, Field as _DataclassField, MISSING as _MISSING
from databind.core.annotations import get_type_annotations
from databind.core.api import Context, ITypeHintAdapter
from databind.core.objectmapper import Module
from databind.core.schema import Field, ISchemaComposer, Schema
from databind.core.types import AnnotatedType, ConcreteType, ObjectType, BaseType, from_typing
from nr import preconditions
from nr.pylang.utils.singletons import NotSet


def enumerate_fields(dataclass_type: t.Type) -> t.Iterator[_DataclassField]:
  preconditions.check_argument(is_dataclass(dataclass_type), 'dataclass_type must be dataclass')
  return iter(dataclass_type.__dataclass_fields__.values())


def dataclass_to_schema(dataclass_type: t.Type, adapter: t.Optional[ITypeHintAdapter] = None) -> Schema:
  preconditions.check_instance_of(dataclass_type, type)
  adapter = adapter or ITypeHintAdapter.Noop()
  fields: t.Dict[str, Field] = {}
  annotations = t.get_type_hints(dataclass_type)
  for field in enumerate_fields(dataclass_type):
    field_type_hint = from_typing(annotations.get(field.name, t.Any)).normalize()
    field_type_hint = adapter.adapt_type_hint(field_type_hint)
    if isinstance(field_type_hint, AnnotatedType):
      field_type_hint, field_annotations = field_type_hint.type, field_type_hint.annotations  # type: ignore  # see https://github.com/python/mypy/issues/9731
    else:
      field_annotations = []
    fields[field.name] = Field(field.name, field_type_hint, field_annotations,
      NotSet.Value if field.default == _MISSING else field.default,
      NotSet.Value if field.default_factory == _MISSING else field.default_factory)
  return Schema(
    dataclass_type.__name__,
    fields,
    list(get_type_annotations(dataclass_type).values()),
    dataclass_type,
    DataclassComposer(dataclass_type)
  )


class DataclassAdapter(Module):

  def adapt_type_hint(self, type_: BaseType, adapter: t.Optional[ITypeHintAdapter] = None) -> BaseType:
    if isinstance(type_, ConcreteType) and is_dataclass(type_.type):
      type_ = ObjectType(dataclass_to_schema(type_.type, adapter))
    return type_


class DataclassComposer(ISchemaComposer):

  def __init__(self, dataclass_type: t.Type) -> None:
    self.dataclass_type = dataclass_type

  def compose(self, data: t.Dict[str, t.Any]) -> t.Any:
    return self.dataclass_type(**data)

  def decompose(self, obj: t.Any) -> t.Dict[str, t.Any]:
    return {f.name: getattr(obj, f.name) for f in enumerate_fields(obj)}
