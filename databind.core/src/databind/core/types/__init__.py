
from .adapter import (
  TypeHintAdapterError,
  TypeHintAdapter,
  DefaultTypeHintAdapter,
  ChainTypeHintAdapter,
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
  UnionSubtypes,
  EntrypointSubtypes,
  DynamicSubtypes,
  ChainSubtypes,
  ImportSubtypes,
  UnionTypeError,
  UnionStyle,
  UnionType,
  union,
  unionclass,
  UnionConverter,
)

import typing as t

#: The global type hint converter.
root = ChainTypeHintAdapter(
  DefaultTypeHintAdapter(),
  UnionConverter(),
  DataclassConverter()
)


def from_typing(type_hint: t.Any, converter: t.Optional['TypeHintAdapter'] = None) -> BaseType:
  converter = converter or root
  return converter.convert_type_hint(type_hint, converter)
