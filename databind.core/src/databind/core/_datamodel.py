
"""
Extends the functionality of the #dataclass module to provide additional metadata for
(de-) serializing data classes.
"""

import types
from dataclasses import dataclass as _dataclass, field as _field, Field as _Field
from typing import Any, Dict, Iterable, List, Optional, Union, T, Tuple, Type, get_type_hints
from ._union import UnionResolver, StaticUnionResolver

__all__ = [
  'UnionMetadata',
  'ModelMetadata',
  'FieldMetadata',
  'uniontype',
  'datamodel',
  'field',
  'enumerate_fields',
]


def _extract_dataclass_from_kwargs(dataclass: Type[T], kwargs: Dict[str, Any]) -> T:
  """
  Internal. Extracts all keyword arguments matching the fields in *dataclass* from the
  dictionary *kwargs* and returns an instance of *dataclass*.
  """

  return dataclass(**{
    field.name: kwargs.pop(field.name)
    for field in dataclass.__dataclass_fields__.values()
    if field.name in kwargs
  })


class UnionResolver: pass


@_dataclass
class _BaseMetadata:
  #: Use strict deserialization mode where that is not already the default.
  strict: bool = _field(default=False)

  #: Use relaxed deserialization mode where that is not already the default.
  relaxed: bool = _field(default=False)

  ATTRIBUTE = '__databind_metadata__'

  @classmethod
  def for_type(cls, type_: Type) -> '_BaseMetadata':
    result = vars(type_).get(cls.ATTRIBUTE)
    if result is None or not isinstance(result, cls):
      result = cls()
    return result


@_dataclass
class UnionMetadata(_BaseMetadata):
  #: The resolver that is used to map type names to a datatype.
  # NOTE(NiklasRosenstein): default=None is needed as otherwise dataclasses complains
  #   that a non-default argument follows a default argument (from the base class).
  resolver: UnionResolver = _field(default=None)

  def __post_init__(self):
    if not self.resolver:
      raise TypeError('"resolver" cannot be None')


@_dataclass
class ModelMetadata(_BaseMetadata):
  #: Allow only keyword arguments when constructing an instance of the model.
  kwonly: bool = _field(default=False)


@_dataclass
class FieldMetadata(_BaseMetadata):
  #: Alternative name of the field used during the (de-) serialization. This may be
  #: set to change the name of a field to a value that is not valid Python syntax
  #: (for example "field-name").
  altname: Optional[str] = _field(default=None)

  #: Set to `True` to indicate that the field is required during deserialization.
  #: This does not indicate that the field is required when constructing the object
  #: in memory, in which case the field's default value is always used.
  required: bool = _field(default=False)

  #: Set to `True` if the field is populated with derived data and should be ignored
  #: during (de-) serialization.
  derived: bool = _field(default=False)

  #: Set to `True` if the type of the field should be flattened into the parent
  #: object when (de-) serializing. There can be only one flattened field on a data
  #: model and it works with other data models as well as dictionaries.
  flatten: bool = _field(default=False)

  #: Indicate that the field should be assigned the raw data from the deserialization.
  #: Setting this to `True` sets #derived to `True` as well.
  raw: bool = _field(default=False)

  #: A list of format specifiers that the (de-) serializer should respect, if applicable
  #: to the field type. Examples of format specifiers would be date format templates for
  #: date types or #decimal.Context for #decimal.Decimal fields.
  formats: List[Any] = _field(default_factory=list)

  KEYSPACE = 'databind.core'

  def __post_init__(self):
    if self.raw:
      self.derived = True

  @classmethod
  def for_field(cls, field: _Field) -> 'FieldMetadata':
    return field.metadata.get(cls.KEYSPACE) or cls()


def uniontype(resolver: Union[UnionMetadata, Dict[str, Type]], **kwargs):
  """
  Decorator for classes to define them as union types, and are to be (de-) serialized as such.
  """

  if isinstance(resolver, dict):
    resolver = StaticUnionResolver(resolver)

  kwargs['resolver'] = resolver
  metadata = UnionMetadata(**kwargs)

  def decorator(cls):
    setattr(cls, UnionMetadata.ATTRIBUTE, metadata)
    return cls

  return decorator


def datamodel(*args, **kwargs):
  """
  This function wraps the #dataclasses.dataclass() decorator. Applicable keyword arguments are
  redirected to the #ModelMetadata which is then set in the `__databind_metadata__` attribute.
  """

  metadata = _extract_dataclass_from_kwargs(ModelMetadata, kwargs)
  result = _dataclass(*args, **kwargs)

  if isinstance(result, types.FunctionType):
    def wrapper(cls):
      cls = result(cls)
      setattr(cls, ModelMetadata.ATTRIBUTE, metadata)
      return cls
    return wrapper

  else:
    setattr(result, ModelMetadata.ATTRIBUTE, metadata)
    return result


def field(*args, **kwargs) -> _Field:
  """
  This function wraps the #dataclasses.field() function, equipping the field with additional
  #FieldMetadata.
  """

  metadata = kwargs.setdefault('metadata', {})
  metadata[FieldMetadata.KEYSPACE] = _extract_dataclass_from_kwargs(FieldMetadata, kwargs)
  return _field(*args, **kwargs)


def enumerate_fields(data_model: Union[T, Type[T]]) -> Iterable[Tuple[str, Type, FieldMetadata]]:
  """
  Enumerate the fields of a datamodel. The items yielded by this generator are tuples of
  the field name, the resolved type hint and the #FieldMetadata.
  """

  if not isinstance(data_model, type):
    data_model = type(data_model)

  type_hints = get_type_hints(data_model)
  for field in data_model.__dataclass_fields__.values():
    yield field.name, type_hints[field.name], FieldMetadata.for_field(field)
