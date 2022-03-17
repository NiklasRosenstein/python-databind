
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


@dataclasses.dataclass
class Schema:
  """ A #Schema describes a set of fields with a name and datatype. """

  #: A dictionary that maps the field descriptions in the schema. The key is the name of the field in code. Given an
  #: instance of an object that complies to a given #Schema, this is the name by which the value of the field should
  #: be read using attribute lookup.
  fields: t.Dict[str, Field]

  #: A function that constructs an instance of a Python object that this schema represents given a dictionary of
  #: the deserialized field values. Fields that are not present in the source payload and a that do not have a default
  #: value will not be present in the passed dictionary.
  constructor: t.Callable[[t.Dict[str, t.Any]], t.Any]


def convert_dataclass_to_schema(dataclass_type: t.Union[t.Type, GenericAlias]) -> Schema:
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
  from databind.core.settings import get_highest_setting, Required

  hint = typeapi.of(dataclass_type)
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

  fields: t.Dict[str, Field] = {}
  for field in dataclasses.fields(dataclass_type):
    if not field.init:
      # If we cannot initialize the field in the constructor, we should also
      # exclude it from the definition of the type for de-/serializing.
      continue

    datatype = typeapi.of(field.type)
    default = NotSet.Value if field.default == MISSING else field.default
    default_factory = NotSet.Value if field.default_factory == MISSING else field.default_factory

    if isinstance(datatype, typeapi.Annotated):
      required = (get_highest_setting(v for v in datatype.metadata if isinstance(v, Required)) or Required(True)).enabled
    else:
      required = default == NotSet.Value and default_factory == NotSet.Value

    # Infuse type parameters, if applicable. We may not have type parameters for the field's origin type if that
    # origion is not a generic type.
    field_origin = field_origins[field.name]
    datatype = typeapi.infuse_type_parameters(datatype, type_parameters.get(field_origin, {}))

    fields[field.name] = Field(
      datatype=datatype,
      required=required,
      default=default,
      default_factory=default_factory,
    )

  return Schema(fields, dataclass_type)
