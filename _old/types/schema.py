
"""
Abstraction for structure schemas that are usually declared using the #dataclasses.dataclass
decorator and possibly ammended with additional information using class and field annotations.
The abstraction helps keeping the serializer implementation separate from the #dataclasses API
and to open it up for the possibility to extend it to other ways of describing the schema.
"""

import dataclasses
import typing as t
import warnings
from dataclasses import is_dataclass, fields as _get_fields, MISSING as _MISSING

from nr.util.optional import Optional
from nr.util.singleton import NotSet

import databind.core.annotations as A
from databind.core.dataclasses import ANNOTATIONS_METADATA_KEY
from databind.core.types.utils import get_type_hints, type_repr
from .adapter import DefaultTypeHintAdapter, TypeContext, TypeHintAdapter, TypeHintAdapterError
from .types import BaseType, ConcreteType, MapType

T = t.TypeVar('T')


@dataclasses.dataclass
class Field:
  """
  Describes a field in a datamodel (aka #Schema).
  """

  #: The name of the field.
  name: str

  #: The type hint associated with this field.
  type: 'BaseType'

  #: A list of the annotations that are associated with the field. Some of the data from these
  #: annotations may be extracted into the other properties on the #Field instance already (such
  #: as #aliases, #required and #flat). The annotations are carried into the field for extension.
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

  #: The default value for the field.
  default: t.Union[NotSet, t.Any] = NotSet.Value

  #: A factory for the default value of the field.
  default_factory: t.Union[NotSet, t.Callable[[], t.Any]] = NotSet.Value

  def __post_init__(self) -> None:
    assert isinstance(self.annotations, list)
    assert isinstance(self.type, BaseType), self.type
    if self.flat and not isinstance(self.type, (ObjectType, MapType)):
      raise RuntimeError('fieldinfo(flat=True) can only be enabled for ObjectType or MapType fields, '
          f'{self.name!r} is of type {self.type!r}')

  def get_annotation(self, annotation_cls: t.Type[T]) -> t.Optional[T]:
    return A.get_annotation(self.annotations, annotation_cls, None) or \
      A.get_annotation(self.type.annotations, annotation_cls, None)

  @property
  def aliases(self) -> t.Sequence[str]:
    """
    The aliases for the field. Aliases are used to look up the value during deserialization in
    the mapping. If specified, the #name is never used during de/serialization except for
    constructing the Python object. The first alias is used as the target name during
    serialization.
    """

    ann = self.get_annotation(A.alias)
    if ann is None:
      return []
    return ann.aliases

  @property
  def required(self) -> t.Optional[bool]:
    """
    Marks the field as required during deserialization, even if the #type marks the field
    as nullable/optional.
    """

    return Optional(self.get_annotation(A.fieldinfo)).map(lambda f: f.required).or_else(False)

  @property
  def flat(self) -> t.Optional[bool]:
    """
    Specifies if the fields of the value in this field are to be embedded flat into the
    parent structure. This is only respected for fields where the #type is #ObjectType or
    #MapType.
    """

    return Optional(self.get_annotation(A.fieldinfo)).map(lambda f: f.flat).or_else(False)

  @property
  def datefmt(self) -> t.Optional['A.datefmt']:
    """
    Returns the date format that is configured for the field via an annotation.
    """

    return self.get_annotation(A.datefmt)

  @property
  def precision(self) -> t.Optional['A.precision']:
    """
    Returns the decimal context that is configured for the field via an annotation.
    """

    return self.get_annotation(A.precision)

  def get_default(self) -> t.Union[NotSet, t.Any]:
    if self.default_factory is not NotSet.Value:
      return self.default_factory()
    return self.default


@dataclasses.dataclass
class Schema:
  """
  Represents a structured object that contains a set of defined #Field#s and can be constructed
  from a dictionary of values matching the fields and deconstructed into such a dictionary for
  subsequent serialization.
  """

  #: The name of the schema (usually the name of the dataclass).
  name: str

  #: A dictionary for the #Field#s of the schema.
  fields: t.Dict[str, Field] = dataclasses.field(repr=False)

  #: Annotations for the schema.
  annotations: t.List[t.Any]

  #: The underlying Python type of the schema.
  python_type: t.Type

  def __post_init__(self) -> None:
    self._flattened: t.Optional[FlattenedSchema] = None
    self.flattened()  # To immediately raise #SchemaDefinitionError on bad flat fields.

  @property
  def typeinfo(self) -> t.Optional['A.typeinfo']:
    return A.get_annotation(self.annotations, A.typeinfo, None)

  @property
  def union(self) -> t.Optional['A.union']:
    return A.get_annotation(self.annotations, A.union, None)

  class _FieldInfo(t.NamedTuple):
    group: str
    path: str
    field: Field

  def flattened(self) -> 'FlattenedSchema':
    """
    Returns the flattened version of this schema which is useful for the de-/serialization logic.
    """

    if self._flattened is not None:
      return self._flattened

    result = FlattenedSchema(self, {}, None)
    for name, field in self.fields.items():
      if field.flat:
        if isinstance(field.type, ObjectType):
          result.extend(name, field.type.schema.flattened())
          continue
        if isinstance(field.type, MapType):
          if result.remainder_field is not None:
            raise SchemaDefinitionError(f'Found multiple flat MapType fields (aka remainder fields) in schema {self.name!r}')
          result.remainder_field = field
          continue
        warnings.warn(f'Field {name!r} of schema {self.name!r} is marked as flat but the annotation is not '
          f'supported for fields of type {field.type!r}. The field will be treated as non-flat.', UserWarning)
      result.add_field(name, self, name, PropagatedField(self, field, None, [name]))

    self._flattened = result
    return result


class PropagatedField(t.NamedTuple):
  """
  Represents a field that may have been propagated from another field (i.e. that field was marked
  as flat, thus all of it's fields are propagated into the parent schema). If a field was not
  propagated from another field, it's #path and #group will be `$`.
  """

  #: The #Schema that the field belongs to.
  schema: Schema

  #: The original #Field object.
  field: Field

  #: The group that the schema belongs to. This is #None for a field that was not propagated,
  #: (ie. #schema is the "root" schema that was flattened), or the name of the field that this
  #: field was propagated from. For fields that are propagated from multiple levels of flattened
  #: fields, the group will only name the immediate field name of the "root" schema.
  group: t.Optional[str]

  #: The path of the propagated field to find starting at the "root" schema.
  path: t.List[str]

  def format_path(self) -> str:
    return '$' if not self.path else '$.' + '.'.join(self.path)


@dataclasses.dataclass
class FlattenedSchema:
  """
  Represents a #Schema after evaluating all proper fields annotated with #A.fieldinfo(flat=True).
  """

  #: The original schema.
  schema: Schema

  #: All fields from a #Schema and potentially the fields of it's own fields of those where
  #: marked as flat.
  fields: t.Dict[str, PropagatedField]

  #: The one field that is a #MapType field and is marked flat.
  remainder_field: t.Optional[Field]

  def add_field(self, origin_field_name: str, origin_schema: Schema, name: str, field: PropagatedField) -> None:
    if name in self.fields:
      raise SchemaDefinitionError(f'Conflict when expanding field \'{origin_schema.name}.{name}\' into '
        f'{self.schema.name!r} (from \'{self.schema.name}.{origin_field_name}\'): '
        f'{self.fields[name].format_path()}, {field.format_path()}')
    self.fields[name] = field

  def extend(self, field_name: str, schema: 'FlattenedSchema') -> None:
    if schema.remainder_field:
      raise SchemaDefinitionError(f'Cannot expand schema with remainder_field ({schema.remainder_field.name}) into '
        f'another schema.')
    for name, field in schema.fields.items():
      self.add_field(field_name, schema.schema, name, PropagatedField(
        field.schema, field.field, field_name, [field_name] + field.path))


class SchemaDefinitionError(Exception):
  pass


@dataclasses.dataclass
class ObjectType(BaseType):
  """
  Represents a type hint for a datamodel (or #Schema). Instances of this type hint are usually
  constructed in a later stage via the #DataclassAdapter() when a #Concrete type hint was encountered
  that can be interpreted as an #ObjectType.
  """

  schema: 'Schema'
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

  def __repr__(self) -> str:
    return f'ObjectType({type_repr(self.schema.python_type)})'

  def to_typing(self) -> t.Any:
    return self.schema.python_type

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(self)


def dataclass_to_schema(dataclass_type: t.Type, context: t.Union[TypeContext, TypeHintAdapter, None] = None) -> Schema:
  """
  Converts the given *dataclass_type* to a #Schema. The dataclass fields are converted to #BaseType#s
  via the given *type_hint_adapter*. If no adapter is specified, the #DefaultTypeHintAdapter will be
  used (note that this adapter does _not_ expand #ConcreteType#s of dataclasses to #ObjectType#s).
  """

  assert isinstance(dataclass_type, type), repr(dataclass_type)
  assert is_dataclass(dataclass_type), 'expected @dataclass type'

  if context is None:
    context = TypeContext(DefaultTypeHintAdapter()).with_scope_of(dataclass_type)
  elif isinstance(context, TypeHintAdapter):
    context = TypeContext(context).with_scope_of(dataclass_type)
  else:
    assert isinstance(context, TypeContext), type(context)

  fields: t.Dict[str, Field] = {}
  annotations = get_type_hints(dataclass_type)

  for field in _get_fields(dataclass_type):
    if not field.init:
      # If we cannot initialize the field in the constructor, we should also
      # exclude it from the definition of the type for de-/serializing.
      continue

    # NOTE (NiklasRosenstein): We do not use #field.type because if it contains a #t.ForwardRef,
    #   it will not be resolved and we can't convert that to our type representation.
    field_type_hint = context.adapt_type_hint(annotations[field.name])
    field_annotations = list(field.metadata.get(ANNOTATIONS_METADATA_KEY, []))

    # Handle field(metadata={'alias': ...}). The value can be a string or list of strings.
    if not any(isinstance(x, A.alias) for x in field_annotations):
      if 'alias' in field.metadata:
        aliases = field.metadata['alias']
        if isinstance(aliases, str):
          aliases = [aliases]
        field_annotations.append(A.alias(*aliases))

    field_default_factory = field.default_factory  # type: ignore
    fields[field.name] = Field(
      field.name,
      field_type_hint,
      field_annotations,
      NotSet.Value if field.default == _MISSING else field.default,
      NotSet.Value if field_default_factory == _MISSING else field_default_factory)

  return Schema(
    dataclass_type.__name__,
    fields,
    list(A.get_type_annotations(dataclass_type).values()),
    dataclass_type,
  )


class DataclassAdapter(TypeHintAdapter):
  """
  Understands #ConcreteType annotations for #@dataclasses.dataclass decorated classes and converts
  them to an #ObjectType.
  """

  def __init__(self) -> None:
    self._cache: t.Dict[t.Type, Schema] = {}

  def adapt_type_hint(self, type_hint: t.Any, context: TypeContext) -> BaseType:
    if isinstance(type_hint, ConcreteType) and is_dataclass(type_hint.type):
      # TODO (@NiklasRosenstein): This is a hack to get around recursive type definitions.
      cache_key = context.apply_type_vars(type_hint.type)
      if cache_key in self._cache:
        return ObjectType(self._cache[cache_key], type_hint.annotations)
      schema = Schema(type_hint.type.__name__, {}, [], type_hint.type)
      self._cache[cache_key] = schema
      try:
        vars(schema).update(vars(dataclass_to_schema(type_hint.type, context.with_scope_of(cache_key))))
      except:
        del self._cache[cache_key]
        raise
      return ObjectType(schema, type_hint.annotations)
    raise TypeHintAdapterError(self, str(type_hint))
