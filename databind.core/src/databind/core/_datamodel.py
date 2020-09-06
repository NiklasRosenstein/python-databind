
"""
Extends the functionality of the #dataclass module to provide additional metadata for
(de-) serializing data classes.
"""

import types
import textwrap
from typing import (Any, Callable, Dict, Iterable, List, Optional, Union, Tuple, Type, TypeVar,
  cast, get_type_hints)

from dataclasses import dataclass as _dataclass, field as _field, Field as _Field, _MISSING_TYPE

from ._typing import type_repr
from ._union import UnionResolver, StaticUnionResolver

T = TypeVar('T')
T_BaseMetadata = TypeVar('T_BaseMetadata', bound='BaseMetadata')
TypeHint = Any  # Supposed to represent the type of a Python type hint.
uninitialized = object()  # Placeholder object to inidicate that a field does not actually have a default.

__all__ = [
  'UnionMetadata',
  'ModelMetadata',
  'FieldMetadata',
  'uniontype',
  'datamodel',
  'field',
  'enumerate_fields',
  'is_datamodel',
  'is_uniontype',
  'TypeHint',
]


def _extract_dataclass_from_kwargs(dataclass: Type[T], kwargs: Dict[str, Any]) -> T:
  """
  Internal. Extracts all keyword arguments matching the fields in *dataclass* from the
  dictionary *kwargs* and returns an instance of *dataclass*.
  """

  return dataclass(**{  # type: ignore
    field.name: kwargs.pop(field.name)
    for field in dataclass.__dataclass_fields__.values()  # type: ignore
    if field.name in kwargs
  })


def _field_has_default(field: _Field) -> bool:
  return any(not isinstance(x, _MISSING_TYPE) for x in (field.default, field.default_factory))  # type: ignore


def _field_get_default(field: _Field) -> Any:
  if not isinstance(field.default, _MISSING_TYPE):  # type: ignore
    return field.default
  if not isinstance(field.default_factory, _MISSING_TYPE):  # type: ignore
    return field.default_factory()  # type: ignore
  raise RuntimeError('{!r} has no default'.format(field))


@_dataclass
class BaseMetadata:
  #: Use strict deserialization mode where that is not already the default.
  strict: bool = _field(default=False)

  #: Use relaxed deserialization mode where that is not already the default.
  relaxed: bool = _field(default=False)

  ATTRIBUTE = '__databind_metadata__'

  @classmethod
  def for_type(cls: Type[T_BaseMetadata], type_: Type) -> T_BaseMetadata:
    try:
      result = vars(type_).get(cast(BaseMetadata, cls).ATTRIBUTE)
    except TypeError:
      return cls()
    if result is None or not isinstance(result, cls):
      result = cls()
    return result


@_dataclass
class ModelMetadata(BaseMetadata):
  #: Allow only keyword arguments when constructing an instance of the model.
  kwonly: bool = _field(default=False)

  #: A type definition which overrides the type for deserializing/serializing the datamodel.
  serialize_as: Union[Callable[[], TypeHint], TypeHint, None] = None


@_dataclass
class FieldMetadata(BaseMetadata):
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

  #: The original #_Field that this #FieldMetadata is associated with. This may not be set
  #: if the #FieldMetadata is instantiated at the top level. NOTE: We should use a weak
  #: reference here, but the #_Field class is not compatible with weakrefs.
  _owning_field: 'Optional[_Field]' = _field(default=None)

  #: Metadata that supplements the original #_Field's metadata. When a #FieldMetadata is
  #: instantiated for a field in a #datamodel, the metadata will be set to the metadata
  #: of the #_Field.
  metadata: Dict[str, Any] = _field(default_factory=dict)

  KEYSPACE = 'databind.core'

  def __post_init__(self):
    if self.raw:
      self.derived = True

  @classmethod
  def for_field(cls, field: _Field) -> 'FieldMetadata':
    return field.metadata.get(cls.KEYSPACE) or cls(_owning_field=field)


def datamodel(*args, **kwargs):
  """
  This function wraps the #dataclasses.dataclass() decorator. Applicable keyword arguments are
  redirected to the #ModelMetadata which is then set in the `__databind_metadata__` attribute.
  """

  metadata = _extract_dataclass_from_kwargs(ModelMetadata, kwargs)
  no_default_fields = []

  def _before_dataclass(cls):
    # Allow non-default arguments to follow default-arguments.
    for key in getattr(cls, '__annotations__', {}).keys():
      if not hasattr(cls, key):
        f = field()
        setattr(cls, key, f)
      else:
        f = getattr(cls, key)
        if not isinstance(f, _Field):
          continue
      if not _field_has_default(f):
        # This prevents a SyntaxError if non-default arguments follow default arguments.
        f.default = uninitialized
        no_default_fields.append(key)

    # Override the `__post_init__` method that is called by the dataclass `__init__`.
    old_postinit = getattr(cls, '__post_init__', None)
    def __post_init__(self):
      # Ensure that no field has a "uninitialized" value.
      for key in self.__dataclass_fields__.keys():
        if getattr(self, key) == uninitialized:
          raise TypeError(f'missing required argument {key!r}')
      if old_postinit:
        old_postinit(self)
    cls.__post_init__ = __post_init__

    return cls

  def _after_dataclass(cls):
    setattr(cls, ModelMetadata.ATTRIBUTE, metadata)

    if metadata.kwonly:
      old_init = cls.__init__
      def __init__(self, **kwargs):
        old_init(self, **kwargs)
      cls.__init__ = __init__

    for key in no_default_fields:
      if getattr(cls, key, None) is uninitialized:
        delattr(cls, key)

    return cls

  if args:
    _before_dataclass(args[0])

  result = _dataclass(*args, **kwargs)

  if not args:
    def wrapper(cls):
      return _after_dataclass(result(_before_dataclass(cls)))
    return wrapper

  return _after_dataclass(result)


def field(*args, **kwargs) -> _Field:
  """
  This function wraps the #dataclasses.field() function, equipping the field with additional
  #FieldMetadata.
  """

  metadata = kwargs.pop('metadata', {})
  field_metadata = _extract_dataclass_from_kwargs(FieldMetadata, kwargs)
  metadata[FieldMetadata.KEYSPACE] = field_metadata
  kwargs['metadata'] = metadata
  field = _field(*args, **kwargs)
  field_metadata._owning_field = field
  field_metadata.metadata = field.metadata
  return field


@_dataclass
class _EnumeratedField:
  field: _Field = _field(repr=False)
  name: str
  type: Type
  metadata: FieldMetadata = _field(repr=False)

  def has_default(self) -> bool:
    return _field_has_default(self.field)

  def get_default(self) -> Any:
    return _field_get_default(self.field)


def enumerate_fields(data_model: Union[T, Type[T]]) -> Iterable[_EnumeratedField]:
  """
  Enumerate the fields of a datamodel. The items yielded by this generator are tuples of
  the field name, the resolved type hint and the #FieldMetadata.
  """

  if not isinstance(data_model, type):
    data_model = type(data_model)

  type_hints = get_type_hints(data_model)
  for field in data_model.__dataclass_fields__.values():  # type: ignore
    yield _EnumeratedField(field, field.name, type_hints[field.name], FieldMetadata.for_field(field))


def is_datamodel(obj: Any) -> bool:
  return isinstance(BaseMetadata.for_type(obj), ModelMetadata)


@datamodel
class UnionMetadata(BaseMetadata):
  #: The resolver that is used to map type names to a datatype. If no resolver is set,
  #: the union type acts as a container for exactly one of it's dataclass fields.
  resolver: UnionResolver

  #: Indicates whether the union type is a container for its members.
  container: bool = _field(default=False)

  #: The type field of the union container.
  type_field: Optional[str] = _field(default=None)

  #: The key in the data structure that identifies the union type. Defaults to "type".
  type_key: str = _field(default='type')

  #: Whether union members should be converted from Python to flat data strucutres.
  #: This option is required in order to de-serialize union members that cannot be
  #: deserialized from mappings (like plain types). The default is `True`.
  flat: bool = _field(default=True)


def uniontype(
  resolver: Union[UnionResolver, Dict[str, Type], Type] = None,
  container: bool = False,
  type_field: str = None,
  **kwargs
):
  """
  Decorator for classes to define them as union types, and are to be (de-) serialized as such.
  Union types can either act as placeholders or as containers for their members.

  If a *resolver* is specified or *container* is `False`, the union type will act as a placeholder
  and will be converted directly into one the union member types. If no *resolver* is specified,
  the members will be determined from the type hints.

  If *container* is #True, the union type will be equipped as a container for its members
  based on the type hints. The *type_field* will be used to store the type name in the
  container.
  """

  cls = None
  if isinstance(resolver, type):
    resolver, cls = None, resolver
    #import pdb; pdb.set_trace()

  if container:
    if not type_field:
      type_field = kwargs.get('type_key', 'type')
    kwargs.setdefault('type_key', type_field)

  if resolver is not None:
    if container:
      raise TypeError('"container" argument cannot be combined with "resolver" argument')
    if type_field is not None:
      raise TypeError('"type_field" argument cannot be combined with "resolver" argument')
    if isinstance(resolver, dict):
      resolver = StaticUnionResolver(resolver)

  def _init_as_container(cls, type_hints):
    """
    Initializes *cls* as a container for the union type members.
    """

    scope = {}
    exec(textwrap.dedent(f"""
      def __init__(self, {type_field}: str, value: Any) -> None:
        self.{type_field} = {type_field}
        self._value = value
      def __repr__(self) -> str:
        return f'{{type(self).__name__}}({{self.{type_field}!r}}, {{self._value!r}})'
      def __eq__(self, other) -> bool:
        if isinstance(other, cls):
          return self.{type_field} == other.{type_field} and self._value == other._value
        return False
      def __ne__(self, other) -> bool:
        if isinstance(other, cls):
          return self.{type_field} != other.{type_field} or self._value != other._value
        return True
    """), {'Any': Any, 'cls': cls}, scope)

    for key, value in scope.items():
      if key not in vars(cls):
        setattr(cls, key, scope[key])

    def _make_property(type_name: str, annotation: Any) -> property:
      def getter(self) -> annotation:  # type: ignore
        assert type_field is not None
        has_type = getattr(self, type_field)
        if has_type != type_name:
          raise TypeError(f'{type_repr(cls)}.{type_name} cannot be accessed if {type_field} == {has_type!r}')
        return self._value
      def setter(self, value: annotation) -> None:  # type: ignore
        assert type_field is not None
        setattr(self, type_field, type_name)
        self._value = value
      return property(getter, setter)

    for key, annotation in type_hints.items():
      setattr(cls, key, _make_property(key, annotation))

    return cls

  def _prevent_init(cls):
    def __init__(self, *args, **kwargs):
      raise TypeError(f'non-container @uniontype {type_repr(cls)} cannot be constructed directly')
    if '__init__' not in vars(cls):
      cls.__init__ = __init__

  def decorator(cls):
    nonlocal resolver
    if not resolver or container:
      type_hints = get_type_hints(cls)
    if not resolver:
      resolver = StaticUnionResolver(type_hints)
    if container:
      _init_as_container(cls, type_hints)
    else:
      _prevent_init(cls)

    kwargs['resolver'] = resolver
    kwargs['container'] = container
    kwargs['type_field'] = type_field
    setattr(cls, UnionMetadata.ATTRIBUTE, UnionMetadata(**kwargs))

    return cls

  if cls:
    return decorator(cls)

  return decorator


def is_uniontype(obj: Any) -> bool:
  return isinstance(BaseMetadata.for_type(obj), UnionMetadata)
