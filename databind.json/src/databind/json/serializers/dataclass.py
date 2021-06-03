
import typing as t
from dataclasses import is_dataclass, Field as _DataclassField
from databind.core.api import Context, DeserializerEnvironment, IDeserializer, ISerializer, SerializerEnvironment
from databind.core.objectmapper import IModule
from databind.core.schema import Field, ISchemaComposer, Schema
from databind.core.typehint import Annotated, Concrete, Datamodel, TypeHint, from_typing
from nr import preconditions


def enumerate_fields(dataclass_type: t.Type) -> t.Iterator[_DataclassField]:
  preconditions.check_argument(is_dataclass(dataclass_type), 'dataclass_type must be dataclass')
  return iter(dataclass_type.__dataclass_fields__.values())


def dataclass_to_schema(dataclass_type: t.Type) -> Schema:
  preconditions.check_instance_of(dataclass_type, t.Type)
  fields: t.Dict[str, Field] = {}
  annotations = t.get_type_hints(dataclass_type)
  for field in enumerate_fields(dataclass_type):
    field_type_hint = from_typing(annotations.get(field.name, t.Any)).normalize()
    if isinstance(field_type_hint, Annotated):
      field_type_hint, field_annotations = field_type_hint.type, field_type_hint.annotations
    else:
      field_annotations = []
    fields[field.name] = Field(field.name, field_type_hint, field_annotations)
  return Schema(
    dataclass_type.__name__,
    fields,
    dataclass_type,
    DataclassComposer(dataclass_type)
  )


class DataclassModule(IModule):

  # IModule
  def get_deserializer(self, type: TypeHint) -> IDeserializer:
    if isinstance(type, Concrete) and is_dataclass(type.type):
      return DataclassDeser()
    return None

  # IModule
  def get_serializer(self, type: TypeHint) -> ISerializer:
    return self.get_deserializer(type)

  # IModule
  def adapt_type_hint(self, type: TypeHint) -> TypeHint:
    if isinstance(type, Concrete) and is_dataclass(type.type):
      type = Datamodel(dataclass_to_schema(type.type))
    return type


class DataclassComposer(ISchemaComposer):

  def __init__(self, dataclass_type: t.Type) -> None:
    self.dataclass_type = dataclass_type

  def compose(self, data: t.Dict[str, t.Any]) -> t.Any:
    return self.dataclass_type(**data)

  def decompose(self, obj: t.Any) -> t.Dict[str, t.Any]:
    return {f.name: getattr(obj, f.name) for f in enumerate_fields(obj)}


class DataclassDeser(IDeserializer, ISerializer):

  def deserialize(self, ctx: Context[DeserializerEnvironment]) -> t.Any:
    raise NotImplementedError  # TODO

  def serialize(self, ctx: Context[SerializerEnvironment]) -> t.Any:
    raise NotImplementedError  # TODO
