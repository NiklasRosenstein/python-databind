
"""
The #DataclassModule provides the type adaptation for classes decorated with `@dataclass` to be
interpreted as a datamodel.
"""

import sys
import typing as t
from dataclasses import is_dataclass, fields as _get_fields, MISSING as _MISSING
from databind.core.dataclasses import ANNOTATIONS_METADATA_KEY  # type: ignore
from databind.core.annotations import get_type_annotations
from databind.core.annotations.alias import alias
from databind.core.api import Context, ITypeHintAdapter
from databind.core.objectmapper import Module
from databind.core.schema import Field, Schema
from databind.core.types import AnnotatedType, ConcreteType, ObjectType, BaseType, from_typing
from nr import preconditions
from nr.pylang.utils.singletons import NotSet


def _get_type_hints(type_: t.Any) -> t.Any:
  if sys.version_info >= (3, 9):
    return t.get_type_hints(type_, include_extras=True)
  else:
    return t.get_type_hints(type_)


def dataclass_to_schema(dataclass_type: t.Type, adapter: t.Optional[ITypeHintAdapter] = None) -> Schema:
  preconditions.check_instance_of(dataclass_type, type)
  adapter = adapter or ITypeHintAdapter.Noop()
  fields: t.Dict[str, Field] = {}
  annotations = _get_type_hints(dataclass_type)

  for field in _get_fields(dataclass_type):
    if not field.init:
      # If we cannot initialize the field in the constructor, we should also
      # exclude it from the definition of the type for de-/serializing.
      continue

    field_type_hint = from_typing(annotations.get(field.name, t.Any))
    field_type_hint = adapter.adapt_type_hint(field_type_hint)
    if isinstance(field_type_hint, AnnotatedType):
      field_type_hint, field_annotations = field_type_hint.type, list(field_type_hint.annotations)  # type: ignore  # see https://github.com/python/mypy/issues/9731
    else:
      field_annotations = []
    field_annotations += field.metadata.get(ANNOTATIONS_METADATA_KEY, [])

    # Handle field(metadata={'alias': ...}). The value can be a string or list of strings.
    if not any(isinstance(x, alias) for x in field_annotations):
      if 'alias' in field.metadata:
        aliases = field.metadata['alias']
        if isinstance(aliases, str):
          aliases = [aliases]
        field_annotations.append(alias(*aliases))

    fields[field.name] = Field(field.name, field_type_hint, field_annotations,
      NotSet.Value if field.default == _MISSING else field.default,
      NotSet.Value if field.default_factory == _MISSING else field.default_factory)  # type: ignore

  return Schema(
    dataclass_type.__name__,
    fields,
    list(get_type_annotations(dataclass_type).values()),
    dataclass_type,
  )


class DataclassAdapter(Module):

  def __init__(self) -> None:
    self._cache: t.Dict[t.Type, ObjectType] = {}

  depth = 0
  def adapt_type_hint(self, type_: BaseType, adapter: t.Optional[ITypeHintAdapter] = None) -> BaseType:
    if isinstance(type_, ConcreteType) and is_dataclass(type_.type):
      # TODO (@NiklasRosenstein): This is a hack to get around recursive type definitions.
      if type_.type in self._cache:
        return self._cache[type_.type]
      new_type = ObjectType(Schema(type_.type.__name__, {}, [], type_.type))
      self._cache[type_.type] = new_type
      new_type.schema = dataclass_to_schema(type_.type, adapter)
      return new_type
    return type_
