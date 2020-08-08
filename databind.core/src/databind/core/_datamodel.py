
"""
Extends the functionality of the #dataclass module to provide additional metadata for
(de-) serializing data classes.
"""

import types
from dataclasses import dataclass as _dataclass, field as _field, Field as _Field, _MISSING_TYPE
from typing import Any, Dict, Iterable, List, Optional, Union, T, Tuple, Type, get_type_hints
from ._typing import type_repr
from ._union import UnionResolver, StaticUnionResolver

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
class BaseMetadata:
  #: Use strict deserialization mode where that is not already the default.
  strict: bool = _field(default=False)

  #: Use relaxed deserialization mode where that is not already the default.
  relaxed: bool = _field(default=False)

  ATTRIBUTE = '__databind_metadata__'

  @classmethod
  def for_type(cls, type_: Type) -> 'BaseMetadata':
    try:
      result = vars(type_).get(cls.ATTRIBUTE)
    except TypeError:
      return cls()
    if result is None or not isinstance(result, cls):
      result = cls()
    return result


@_dataclass
class ModelMetadata(BaseMetadata):
  #: Allow only keyword arguments when constructing an instance of the model.
  kwonly: bool = _field(default=False)


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

  KEYSPACE = 'databind.core'

  def __post_init__(self):
    if self.raw:
      self.derived = True

  @classmethod
  def for_field(cls, field: _Field) -> 'FieldMetadata':
    return field.metadata.get(cls.KEYSPACE) or cls()


def datamodel(*args, **kwargs):
  """
  This function wraps the #dataclasses.dataclass() decorator. Applicable keyword arguments are
  redirected to the #ModelMetadata which is then set in the `__databind_metadata__` attribute.
  """

  metadata = _extract_dataclass_from_kwargs(ModelMetadata, kwargs)
  uninitialized = object()  # Placeholder object to inidicate that a field does not actually have a default.

  def _before_dataclass(cls):
    # Allow non-default arguments to follow default-arguments.
    no_default_fields = []
    for key, value in getattr(cls, '__annotations__', {}).items():
      if not hasattr(cls, key):
        f = field()
        setattr(cls, key, f)
      else:
        f = getattr(cls, key)
        if not isinstance(f, _Field):
          continue
      if all(isinstance(x, _MISSING_TYPE) for x in (f.default, f.default_factory)):
        # This prevents a SyntaxError if non-default arguments follow default arguments.
        f.default = uninitialized
        no_default_fields.append(key)

    # Override the `__post_init__` method that is called by the dataclass `__init__`.
    old_postinit = getattr(cls, '__post_init__', None)
    def __post_init__(self):
      # Ensure that no field has a "uninitialized" value.
      for name in no_default_fields:
        if getattr(self, name) == uninitialized:
          raise TypeError(f'missing required argument {name!r}')
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

  metadata = kwargs.setdefault('metadata', {})
  metadata[FieldMetadata.KEYSPACE] = _extract_dataclass_from_kwargs(FieldMetadata, kwargs)
  return _field(*args, **kwargs)


@_dataclass
class _EnumeratedField:
  field: _Field = _field(repr=False)
  name: str
  type: Type
  metadata: FieldMetadata = _field(repr=False)


def enumerate_fields(data_model: Union[T, Type[T]]) -> Iterable[_EnumeratedField]:
  """
  Enumerate the fields of a datamodel. The items yielded by this generator are tuples of
  the field name, the resolved type hint and the #FieldMetadata.
  """

  if not isinstance(data_model, type):
    data_model = type(data_model)

  type_hints = get_type_hints(data_model)
  for field in data_model.__dataclass_fields__.values():
    yield _EnumeratedField(field, field.name, type_hints[field.name], FieldMetadata.for_field(field))


def is_datamodel(obj: Any) -> bool:
  return isinstance(BaseMetadata.for_type(obj), ModelMetadata)


@datamodel
class UnionMetadata(BaseMetadata):
  #: The resolver that is used to map type names to a datatype. If no resolver is set,
  #: the union type acts as a container for exactly one of it's dataclass fields.
  resolver: UnionResolver

  #: The key in the data structure that identifies the union type. Defaults to "type".
  type_key: str = _field(default=str)

  #: Whether union members should be converted from Python to flat data strucutres.
  #: The default is `True`.
  flat: bool = _field(default=True)


def uniontype(resolver: Union[UnionMetadata, Dict[str, Type], Type] = None, type_field: str = None, **kwargs):
  """
  Decorator for classes to define them as union types, and are to be (de-) serialized as such.
  Union types can either act as placeholders or as containers for their members.

  If a *resolver* is specified, the union type will act as a placeholder and will be converted
  directly into one the union member types.

  If no *resolver* is specified, the union type will also be a dataclass, where the union
  type members are derived from the fields. All fields on such a union type must be optional,
  and when converted, only one such field can be set.
  """

  cls = None

  if resolver is None or isinstance(resolver, type):
    resolver, cls = None, resolver
    if not type_field:
      type_field = kwargs.get('type_key', 'type')
    kwargs.setdefault('type_key', type_field)
  else:
    if type_field is not None:
      raise TypeError('"type_field" argument cannot be combined with "resolver" argument')
    if isinstance(resolver, dict):
      resolver = StaticUnionResolver(resolver)

  kwargs['resolver'] = resolver
  metadata = UnionMetadata(**kwargs)

  def _init_as_container(cls):
    """
    Initializes *cls* as a container for the union type members.
    """

    scope = {'Any': Any}
    exec(
      f"def __init__(self, {type_field}: str, value: Any) -> None:\n"
      f"  self.{type_field} = {type_field}\n"
      f"  self._value = value",
      scope)

    if '__init__' not in vars(cls):
      cls.__init__ = scope['__init__']

    def _make_property(type_name: str, annotation: Any) -> property:
      def getter(self) -> annotation:
        has_type = getattr(self, type_field)
        if has_type != type_name:
          raise TypeError(f'{type_repr(cls)}.{type_name} cannot be accessed if {type_field} == {has_type!r}')
        return self._value
      def setter(self, value: annotation) -> None:
        setattr(self, type_field, type_name)
        self._value = value
      return property(getter, setter)

    for key, annotation in get_type_hints(cls).items():
      setattr(cls, key, _make_property(key, annotation))

    return cls

  def decorator(cls):
    if not resolver:
      _init_as_container(cls)
    setattr(cls, UnionMetadata.ATTRIBUTE, metadata)
    return cls

  if cls:
    return decorator(cls)

  return decorator


def is_uniontype(obj: Any) -> bool:
  return isinstance(BaseMetadata.for_type(obj), UnionMetadata)
