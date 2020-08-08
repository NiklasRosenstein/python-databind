
import abc
from dataclasses import dataclass as _dataclass
from typing import Any, Generic, Optional, T, Type, Union
from ._datamodel import (
  _BaseMetadata,
  FieldMetadata,
  ModelMetadata,
  UnionMetadata,
  datamodel,
  uniontype,
)
from ._locator import Locator
from ._typing import type_repr

__all__ = [
  'Context',
  'Converter',
  'UnknownTypeError',
  'Registry',
]


@_dataclass
class Context:
  """
  The context contains data relevant during value conversion, such as metadata coming from
  union types, data models and fields. The context represents a tree, where every element in
  that tree represents a value in the structured data that is being converted.
  """

  parent: Optional['Context']
  registry: 'Registry'
  locator: Locator
  type: Type
  value: Any
  field_metadata: Optional[FieldMetadata]

  @classmethod
  def new(cls, registry: 'Registry', type: Type, value: Any, field_metadata: FieldMetadata=None) -> 'Context':
    return cls(None, registry, Locator([]), type, value, field_metadata)

  def fork(
    self,
    type: Type,
    value: Any,
    field_metadata: FieldMetadata=NotImplemented,
  ) -> 'Context':
    """
    Create a fork in the context tree, re-using the same locator and parent but allowing to
    change the type and value, and optionally the field metadata.
    """

    if field_metadata is NotImplemented:
      field_metadata = self.field_metadata

    return Context(self.parent, self.registry, self.locator, type, value, field_metadata)

  def child(
    self,
    key: Union[int, str],
    type: Type,
    value: Any,
    field_metadata: FieldMetadata=None
  ) -> 'Context':
    """
    Create a new child node in the context tree, advancing to the next sub-structure from the
    current value.
    """

    return Context(self, self.registry, self.locator.push(key), type, value, field_metadata)

  def get_converter(self) -> 'Converter':
    return self.registry.get_converter(self.type)

  def from_python(self) -> Any:
    return self.get_converter().from_python(self.value, self)

  def to_python(self) -> Any:
    return self.get_converter().to_python(self.value, self)


class Converter(Generic[T], metaclass=abc.ABCMeta):
  """
  Abstract base class that convert from and to a Python datatype.
  """

  @abc.abstractmethod
  def from_python(self, value: T, context: Context) -> Any:
    pass

  @abc.abstractmethod
  def to_python(self, value: Any, context: Context) -> T:
    pass


class UnknownTypeError(TypeError):
  pass


class Registry:
  """
  The registry is what maps data types and type hints to #Converter implementations. Types that
  are decorated with #@uniontype() or #@datamodel() are handled special in that they must be
  associated with the respective decorator function.
  """

  def __init__(self, parent: Optional['Registry']) -> None:
    self.parent = parent
    self._mapping = {}

  @property
  def root(self) -> 'Registry':
    if not self.parent:
      return self
    return self.parent.root

  def register_converter(self, type: Type, converter: Converter, overwrite: bool=False) -> None:
    if type in self._mapping and not overwrite:
      raise RuntimeError(f'converter for {type_repr(type)} already registered')
    self._mapping[type] = converter

  def get_converter(self, type: Type) -> Converter:

    # Map type's decoreated with uniontype/datamodel to the respective functions.
    metadata = _BaseMetadata.for_type(type)
    if isinstance(metadata, UnionMetadata):
      type = uniontype
    elif isinstance(metadata, ModelMetadata):
      type = datamodel

    # Resolve type hints to the original annotated form.
    if hasattr(type, '__origin__'):
      type = type.__origin__

    if type in self._mapping:
      return self._mapping[type]

    if self.parent:
      return self.parent.get_converter(type)
    else:
      raise UnknownTypeError(f'no converter found for type {type_repr(type)}')
