
from .converter import (
  ITypeHintConverter,
  DefaultTypeHintConverter,
  ChainTypeHintConverter,
  TypeHintConversionError,
)

from .types import (
  BaseType,
  ConcreteType,
  ImplicitUnionType,
  OptionalType,
  ListType,
  SetType,
  MapType,
  UnknownType,
)

from .schema import (
  Field,
  Schema,
  SchemaDefinitionError,
  ObjectType,
  DataclassConverter,
)

from .union import (
  IUnionSubtypes,
  EntrypointSubtypes,
  DynamicSubtypes,
  ChainSubtypes,
  ImportSubtypes,
  UnionTypeError,
  UnionStyle,
  UnionType,
)

import typing as t
from databind.core.annotations.unionclass import UnionConverter

#: The global type hint converter.
root = ChainTypeHintConverter(
  DefaultTypeHintConverter(),
  UnionConverter(),
  DataclassConverter()
)


def from_typing(type_hint: t.Any, converter: t.Optional['ITypeHintConverter'] = None) -> BaseType:
  converter = converter or root
  return converter.convert_type_hint(type_hint, converter)
