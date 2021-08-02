
"""
Abstraction for structure schemas that are usually declared using the #dataclasses.dataclass
decorator and possibly ammended with additional information using class and field annotations.
The abstraction helps keeping the serializer implementation separate from the #dataclasses API
and to open it up for the possibility to extend it to other ways of describing the schema.
"""

import dataclasses
import sys
import typing as t

import nr.preconditions as preconditions
from nr.optional import Optional
from nr.pylang.utils import NotSet

from .converter import ITypeHintConverter, TypeHintConversionError
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
    _check_no_colliding_flattened_fields(self)

  @property
  def typeinfo(self) -> t.Optional['A.typeinfo']:
    return A.get_annotation(self.annotations, A.typeinfo, None)

  @property
  def union(self) -> t.Optional['A.union']:
    return A.get_annotation(self.annotations, A.union, None)

  class _FlatField(t.NamedTuple):
    group: str
    path: str
    field: Field

  def flat_fields(self) -> t.Iterator[_FlatField]:
    """
    Returns a list of the flattened fields of the schema and the group that they belong to.
    Fields that belong to the root schema (ie. `self`) are grouped under the key `$`.
    """

    stack = [('$', self)]
    while stack:
      path, schema = stack.pop(0)
      for field_name, field in schema.fields.items():
        field_path = path + '.' + field_name
        if not field.flat:
          group = path.split('.')[:2]
          yield Schema._FlatField(group[-1], field_path, field)
        if field.flat and isinstance(field.type, ObjectType):
          stack.append((field_path, field.type.schema))


def _check_no_colliding_flattened_fields(schema: Schema) -> None:
  """
  Checks that there are no colliding fields in the *schema* and it's flattened fields.

  Raises a #SchemaDefinitionError if the constraint is violated.
  """

  fields: t.Dict[str, str] = {}
  for field in schema.flat_fields():
    if field.field.name in fields:
      raise SchemaDefinitionError(f'Flat field conflict in schema {schema.name!r}: ({fields[field.field.name]}, {field.path})')
    fields[field.field.name] = field.path


class SchemaDefinitionError(Exception):
  pass


@dataclasses.dataclass
class ObjectType(BaseType):
  """
  Represents a type hint for a datamodel (or #Schema). Instances of this type hint are usually
  constructed in a later stage after #from_typing() when a #Concrete type hint was encountered
  that can be interpreted as an #ObjectType (see #databind.core.default.dataclass.DataclassModule).
  """

  schema: 'Schema'
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

  def __repr__(self) -> str:
    return f'ObjectType({self.schema.python_type.__name__})'

  def to_typing(self) -> t.Any:
    return self.schema.python_type

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(self)


def _get_type_hints(type_: t.Any) -> t.Any:
  if sys.version_info >= (3, 9):
    return t.get_type_hints(type_, include_extras=True)
  else:
    return t.get_type_hints(type_)


from databind.core.annotations import get_type_annotations
from databind.core.dataclasses import ANNOTATIONS_METADATA_KEY
from dataclasses import is_dataclass, fields as _get_fields, MISSING as _MISSING


def dataclass_to_schema(dataclass_type: t.Type, type_converter: ITypeHintConverter) -> Schema:
  preconditions.check_instance_of(dataclass_type, type)
  preconditions.check_argument(is_dataclass(dataclass_type), 'expected @dataclass type')

  fields: t.Dict[str, Field] = {}
  annotations = _get_type_hints(dataclass_type)

  for field in _get_fields(dataclass_type):
    if not field.init:
      # If we cannot initialize the field in the constructor, we should also
      # exclude it from the definition of the type for de-/serializing.
      continue

    # NOTE (NiklasRosenstein): We do not use #field.type because if it contains a #t.ForwardRef,
    #   it will not be resolved and we can't convert that to our type representation.
    field_type_hint = type_converter(annotations[field.name])
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
    list(get_type_annotations(dataclass_type).values()),
    dataclass_type,
  )


class DataclassConverter(ITypeHintConverter):
  """
  Understands #ConcreteType annotations for #@dataclasses.dataclass decorated classes and converts
  them to an #ObjectType.
  """

  def __init__(self) -> None:
    self._cache: t.Dict[t.Type, Schema] = {}

  def convert_type_hint(self, type_hint: t.Any, recurse: 'ITypeHintConverter') -> 'BaseType':
    if isinstance(type_hint, ConcreteType) and is_dataclass(type_hint.type):
      # TODO (@NiklasRosenstein): This is a hack to get around recursive type definitions.
      if type_hint.type in self._cache:
        return ObjectType(self._cache[type_hint.type], type_hint.annotations)
      schema = Schema(type_hint.type.__name__, {}, [], type_hint.type)
      self._cache[type_hint.type] = schema
      vars(schema).update(vars(dataclass_to_schema(type_hint.type, recurse)))
      return ObjectType(schema, type_hint.annotations)
    raise TypeHintConversionError(self, str(type_hint))


import databind.core.annotations as A
