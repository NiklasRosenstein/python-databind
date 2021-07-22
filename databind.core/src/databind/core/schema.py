
"""
Abstraction for structure schemas that are usually declared using the #dataclasses.dataclass
decorator and possibly ammended with additional information using class and field annotations.
The abstraction helps keeping the serializer implementation separate from the #dataclasses API
and to open it up for the possibility to extend it to other ways of describing the schema.
"""

import abc
import typing as t
from dataclasses import dataclass, field
from databind.core.annotations import get_annotation, alias, datefmt, fieldinfo, precision, typeinfo, unionclass
from databind.core.types import BaseType, MapType, ObjectType
from nr.optional import Optional
from nr.pylang.utils import NotSet


@dataclass
class Field:
  """
  Describes a field in a datamodel (aka #Schema).
  """

  #: The name of the field.
  name: str

  #: The type hint associated with this field.
  type: BaseType

  #: A list of the annotations that are associated with the field. Some of the data from these
  #: annotations may be extracted into the other properties on the #Field instance already (such
  #: as #aliases, #required and #flat). The annotations are carried into the field for extension.
  annotations: t.List[t.Any] = field(default_factory=list)

  #: The default value for the field.
  default: t.Union[NotSet, t.Any] = NotSet.Value

  #: A factory for the default value of the field.
  default_factory: t.Union[NotSet, t.Callable[[], t.Any]] = NotSet.Value

  def __post_init__(self) -> None:
    assert isinstance(self.annotations, list)
    if self.flat and not isinstance(self.type, (ObjectType, MapType)):
      raise RuntimeError('fieldinfo(flat=True) can only be enabled for ObjectType or MapType fields, '
          f'{self.name!r} is of type {self.type!r}')

  @property
  def aliases(self) -> t.Sequence[str]:
    """
    The aliases for the field. Aliases are used to look up the value during deserialization in
    the mapping. If specified, the #name is never used during de/serialization except for
    constructing the Python object. The first alias is used as the target name during
    serialization.
    """

    ann = get_annotation(self.annotations, alias, None)
    if ann is None:
      return []
    return ann.aliases

  @property
  def required(self) -> t.Optional[bool]:
    """
    Marks the field as required during deserialization, even if the #type marks the field
    as nullable/optional.
    """

    return Optional(get_annotation(self.annotations, fieldinfo, None)).map(lambda f: f.required).or_else(False)

  @property
  def flat(self) -> t.Optional[bool]:
    """
    Specifies if the fields of the value in this field are to be embedded flat into the
    parent structure. This is only respected for fields where the #type is #ObjectType or
    #MapType.
    """

    return Optional(get_annotation(self.annotations, fieldinfo, None)).map(lambda f: f.flat).or_else(False)

  @property
  def datefmt(self) -> t.Optional[datefmt]:
    """
    Returns the date format that is configured for the field via an annotation.
    """

    return get_annotation(self.annotations, datefmt, None)

  @property
  def precision(self) -> t.Optional[precision]:
    """
    Returns the decimal context that is configured for the field via an annotation.
    """

    return get_annotation(self.annotations, precision, None)

  def get_default(self) -> t.Union[NotSet, t.Any]:
    if self.default_factory is not NotSet.Value:
      return self.default_factory()
    return self.default


@dataclass
class Schema:
  """
  Represents a structured object that contains a set of defined #Field#s and can be constructed
  from a dictionary of values matching the fields and deconstructed into such a dictionary for
  subsequent serialization.
  """

  #: The name of the schema (usually the name of the dataclass).
  name: str

  #: A dictionary for the #Field#s of the schema.
  fields: t.Dict[str, Field] = field(repr=False)

  #: Annotations for the schema.
  annotations: t.List[t.Any]

  #: The underlying Python type of the schema.
  python_type: t.Type

  def __post_init__(self) -> None:
    _check_no_colliding_flattened_fields(self)

  @property
  def typeinfo(self) -> t.Optional[typeinfo]:
    return get_annotation(self.annotations, typeinfo, None)

  @property
  def unionclass(self) -> t.Optional[unionclass]:
    return get_annotation(self.annotations, unionclass, None)

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
