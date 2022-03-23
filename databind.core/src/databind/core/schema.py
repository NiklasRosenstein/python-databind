
from __future__ import annotations
import dataclasses
import sys
import typing as t

import typeapi
from nr.util.singleton import NotSet

if sys.version_info[:2] <= (3, 8):
  GenericAlias = t.Any
else:
  from types import GenericAlias

if t.TYPE_CHECKING:
  class Constructor(t.Protocol):
    def __call__(self, **kwargs: t.Any) -> t.Any: ...

__all__ = ['Field', 'Schema', 'convert_to_schema', 'convert_dataclass_to_schema', 'convert_typed_dict_to_schema',
  'get_fields_expanded']


@dataclasses.dataclass
class Field:
  """ Describes a field in a schema. """

  #: The datatype of the field.
  datatype: typeapi.Hint

  #: Whether the field is required to be present, if this is `False` and the field does not have a #default or
  #: #default_factorty, the field value will not be passed to the schema constructor. Even if a #default or
  #: #default_factory is present, if he field is required it must be present in the payload being deserialized.
  required: bool = True

  #: The default value for the field, if any.
  default: t.Union[NotSet, t.Any] = NotSet.Value

  #: The default value factory for the field, if any.
  default_factory: t.Union[NotSet, t.Any] = NotSet.Value

  #: Indicates whether the field is to be treated "flat". If the #datatype is a structured type that has fields of its
  #: own, those fields should be treated as if expanded into the same level as this field.
  flattened: bool = False

  def has_default(self) -> bool:
    return self.default is not NotSet.Value or self.default_factory is not NotSet.Value

  def get_default(self) -> t.Any:
    if self.default is not NotSet.Value:
      return self.default
    elif self.default_factory is not NotSet.Value:
      return self.default_factory()
    else:
      raise RuntimeError(f'Field does not have a default value')

  @property
  def aliases(self) -> t.Tuple[str, ...]:
    """ For convience, the aliases described in the #datatype#'s annotations are listed here. Do note however, that
    during the conversion process, the #Alias setting should still be looked up through #Context.get_setting()
    and this field should be ignored. It serves only a introspective purpose. Returns an empty tuple if no alias
    setting is present in the type hint. """

    from databind.core.settings import Alias, get_annotation_setting
    alias = get_annotation_setting(self.datatype, Alias)
    return alias.aliases if alias else ()


@dataclasses.dataclass
class Schema:
  """ A #Schema describes a set of fields with a name and datatype. """

  #: A dictionary that maps the field descriptions in the schema. The key is the name of the field in code. Given an
  #: instance of an object that complies to a given #Schema, this is the name by which the value of the field should
  #: be read using attribute lookup.
  fields: t.Dict[str, Field]

  #: A function that constructs an instance of a Python object that this schema represents given a dictionary as
  #: keyword arguments of the deserialized field values. Fields that are not present in the source payload and a that
  #: do not have a default value will not be present in the passed dictionary.
  constructor: Constructor

  #: The underlying native Python type associated with the schema.
  type: t.Type

  #: Annotation metadata that goes with the schema, possibly derived from a #typeapi.Annotated hint or the underlying
  #: Python type object.
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)


def convert_to_schema(hint: typeapi.Hint) -> Schema:
  """ Convert the given type hint to a #Schema.

  The function delegates to #convert_dataclass_to_schema() or #convert_typed_dict_to_schema().

  Arguments:
    hint: The type hint to convert. If it is a #typeapi.Annotated hint, it will be unwrapped.
  Raises:
    ValueError: If the type hint is not supported.
  """

  assert isinstance(hint, typeapi.Hint), hint
  original_hint = hint

  annotations = []
  if isinstance(hint, typeapi.Annotated):
    annotations = list(hint.metadata)
    hint = hint.wrapped

  if isinstance(hint, typeapi.Type) and dataclasses.is_dataclass(hint.type):
    schema = convert_dataclass_to_schema(hint.type)
  elif isinstance(hint, typeapi.Type) and typeapi.utils.is_typed_dict(hint.type):
    schema = convert_typed_dict_to_schema(hint.type)
  else:
    raise ValueError(f'cannot be converted to a schema: {original_hint}')

  schema.annotations.extend(annotations)
  return schema


def convert_dataclass_to_schema(dataclass_type: t.Union[t.Type, GenericAlias, typeapi.Type]) -> Schema:
  """ Converts a Python class that is decorated with #dataclasses.dataclass().

  The function will respect the #Required setting if it is present in a field's datatype if and only if the
  setting occurs in the root type hint, which must be a #typing.Annotated hint.

  Arguments:
    dataclass_type: A Python type that is a dataclass, or a generic alias of a dataclass.
  Returns:
    A schema that represents the dataclass. If a generic alias was passed, fields of which the type hint contained
    type parameters will have their type parameters substituted with the respective arguments present in the alias.

  Example:

  ```py
  import dataclasses
  import typing as t
  import typeapi
  from databind.core.schema import convert_dataclass_to_schema, Field, Schema
  T = t.TypeVar('T')
  @dataclasses.dataclass
  class A(t.Generic[T]):
    a: T
  assert convert_dataclass_to_schema(A[int]) == Schema({'a': Field(typeapi.of(int))}, A)
  ```
  """

  from dataclasses import MISSING

  if isinstance(dataclass_type, typeapi.Type):
    hint = dataclass_type
  else:
    hint = t.cast(typeapi.Type, typeapi.of(dataclass_type))
    assert isinstance(hint, typeapi.Type), hint

  dataclass_type = hint.type
  assert isinstance(dataclass_type, type), repr(dataclass_type)
  assert dataclasses.is_dataclass(dataclass_type), 'expected @dataclasses.dataclass type'

  # Collect the type parameters of all involved generic classes and which field was declared in which class.
  type_parameters = {t.__origin__: v.get_parameter_mapping() for t, v in hint.get_orig_bases_parametrized(True).items()}
  type_parameters[hint.type] = hint.get_parameter_mapping()
  type_annotations: t.Dict[t.Type, t.Dict[str, t.Any]] = {}
  field_origins: t.Dict[str, t.Type] = {}
  for base in hint.type.__mro__:
    if dataclasses.is_dataclass(base):
      type_annotations[base] = typeapi.get_annotations(base)
      for field in dataclasses.fields(base):
        if field.name in type_annotations[base] and field.name not in field_origins:
          field_origins[field.name] = base

  annotations = typeapi.get_annotations(dataclass_type, include_bases=True)
  fields: t.Dict[str, Field] = {}
  for field in dataclasses.fields(dataclass_type):
    if not field.init:
      # If we cannot initialize the field in the constructor, we should also
      # exclude it from the definition of the type for de-/serializing.
      continue

    datatype = typeapi.eval_types(typeapi.of(annotations[field.name]), globalns=typeapi.scope(dataclass_type))
    default = NotSet.Value if field.default == MISSING else field.default
    default_factory = NotSet.Value if field.default_factory == MISSING else field.default_factory
    required = _is_required(datatype, default == NotSet.Value and default_factory == NotSet.Value)

    # Infuse type parameters, if applicable. We may not have type parameters for the field's origin type if that
    # origin is not a generic type.
    field_origin = field_origins[field.name]
    datatype = typeapi.infuse_type_parameters(datatype, type_parameters.get(field_origin, {}))

    fields[field.name] = Field(
      datatype=datatype,
      required=required,
      default=default,
      default_factory=default_factory,
      flattened=_is_flat(datatype, False),
    )

  return Schema(fields, t.cast('Constructor', dataclass_type), dataclass_type)


def convert_typed_dict_to_schema(typed_dict: typeapi.utils.TypedDict) -> Schema:
  """ Converts the definition of a #typing.TypedDict to a #Schema.

  !!! note

      This function will take into account default values assigned on the class-level of the typed dict (which is
      usually only relevant if the class-style declaration method was used, but default values can be assigned to
      the function-style declared type as well). Fields that have default values are considered not-required even
      if the declaration specifies them as required.

      Be aware that right-hand side values on #typing.TypedDict classes are not allowed by Mypy.

      Also note that #typing.TypedDict cannot be mixed with #typing.Generic, so keys with a generic type in the
      typed dict are not possible (state: 2022-03-17, Python 3.10.2).

  !!! todo

      Support understanding #typing.Required and #typing.NotRequired.

  Example:

  ```py
  from databind.core.schema import convert_typed_dict_to_schema, Schema, Field
  import typing
  class Movie(typing.TypedDict):
    name: str
    year: int = 0
  assert convert_typed_dict_to_schema(Movie) == Schema({
    'name': Field(typeapi.of(str)),
    'year': Field(typeapi.of(int), False, 0),
  }, Movie)
  ```
  """

  assert typeapi.utils.is_typed_dict(typed_dict), typed_dict

  annotations = typeapi.get_annotations(typed_dict)
  fields: t.Dict[str, Field] = {}
  for key in typed_dict.__required_keys__ | typed_dict.__optional_keys__:
    datatype = typeapi.eval_types(typeapi.of(annotations[key]), globalns=typeapi.scope(t.cast(type, typed_dict)))
    has_default = hasattr(typed_dict, key)
    required = _is_required(datatype, False if has_default else typed_dict.__total__)
    fields[key] = Field(
      datatype=datatype,
      required=required,
      default=getattr(typed_dict, key) if has_default else NotSet.Value,
      flattened=_is_flat(datatype, False),
    )

  return Schema(fields, t.cast('Constructor', typed_dict), t.cast(t.Type, typed_dict))


def _is_required(datatype: typeapi.Hint, default: bool) -> bool:
  """ If *datatype* is a #typeapi.Annotated instance, it will look for a #Required settings instance and returns
  that instances #Required.enabled value. Otherwise, it returns *default*. """
  from databind.core.settings import get_annotation_setting, Required
  return (get_annotation_setting(datatype, Required) or Required(default)).enabled


def _is_flat(datatype: typeapi.Hint, default: bool) -> bool:
  from databind.core.settings import get_annotation_setting, Flattened
  return (get_annotation_setting(datatype, Flattened) or Flattened(default)).enabled


def get_fields_expanded(
  schema: Schema,
  convert_to_schema: t.Callable[[typeapi.Hint], Schema] = convert_to_schema,
) -> t.Dict[str, t.Dict[str, Field]]:
  """ Returns a dictionary that contains an entry for each flattened field in the schema, mapping to another
  dictionary that contains _all_ fields expanded from the flattened field's sub-schema.

  Given a schema like the following example, this function returns something akin to the below.

  === "Schema"

      ```
      Schema1:
        a: int
        b: Schema2, flattened=True

      Schema2:
        c: str
        d: Schema3, flattened=True

      Schema3:
        e: int
      ```

  === "Result"

      ```py
      {
        "b": {
          "c": Field(str),
          "e": Field(int)
        }
      }

  Arguments:
    schema: The schema to compile the expanded fields for.
    convert_to_schema: A function that accepts a #typeapi.Hint and converts it to a schema.
      Defaults to the #convert_to_schema() function.

  !!! note

      The top-level dictionary returned by this function contains _only_ those fields that are
      flattened and should be "composed" of other fields.
  ```
  """

  result = {}
  for field_name, field in schema.fields.items():
    if field.flattened:
      field_schema = convert_to_schema(field.datatype)
      result[field_name] = {
        **{k: v for k, v in field_schema.fields.items() if not v.flattened},
        **{k: v for sf in get_fields_expanded(field_schema).values() for k, v in sf.items()},
      }
      for sub_field_name in result[field_name]:
        if sub_field_name in schema.fields and sub_field_name != field_name:
          raise RuntimeError(f'field {sub_field_name!r} occurs multiple times')
  return result
