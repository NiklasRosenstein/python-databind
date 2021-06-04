
"""
Abstraction for structure schemas that are usually declared using the #dataclasses.dataclass
decorator and possibly ammended with additional information using class and field annotations.
The abstraction helps keeping the serializer implementation separate from the #dataclasses API
and to open it up for the possibility to extend it to other ways of describing the schema.
"""

import abc
import decimal
import typing as t
from dataclasses import dataclass, field
from databind.core.annotations import get_annotation, alias, typeinfo, unionclass
from databind.core.typehint import TypeHint

# TODO(NiklasRosenstein): Implement more of the Field properties


@dataclass
class Field:
  """
  Describes a field in a datamodel (aka #Schema).
  """

  #: The name of the field.
  name: str

  #: The type hint associated with this field.
  typehint: TypeHint

  #: A list of the annotations that are associated with the field. Some of the data from these
  #: annotations may be extracted into the other properties on the #Field instance already (such
  #: as #aliases, #required and #flat). The annotations are carried into the field for extension.
  annotations: t.List[t.Any]

  @property
  def aliases(self) -> t.List[str]:
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
  def required(self) -> bool:
    """
    Marks the field as required during deserialization, even if the #typehint marks the field
    as nullable/optional.
    """

    return False

  @property
  def flat(self) -> bool:
    """
    Specifies if the fields of the value in this field are to be embedded flat into the
    parent structure. This is only respected for fields where the #typehint represents a
    dataclass or mapping.
    """

    return False

  @property
  def date_format(self) -> t.Optional[str]:
    """
    Returns the date format that is configured for the field via an annotation.
    """

    return None

  @property
  def datetime_format(self) -> t.Optional[str]:
    """
    Returns the datetime format that is configured for the field via an annotation.
    """

    return None

  @property
  def decimal_context(self) -> t.Optional[decimal.Context]:
    """
    Returns the decimal context that is configured for the field via an annotation.
    """

    return None


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

  #: An object that acts as a composer and decomposer for instances of the #python_type.
  composer: 'ISchemaComposer' = field(repr=False)

  @property
  def typeinfo(self) -> t.Optional[typeinfo]:
    return get_annotation(self.annotations, typeinfo, None)

  @property
  def unionclass(self) -> t.Optional[unionclass]:
    return get_annotation(self.annotations, unionclass, None)


class ISchemaComposer(metaclass=abc.ABCMeta):
  """
  This class acts as the interface to construct and decompose Python objects from/to dictionaries.
  The values in the dictionaries are still normal Python values and not in a pre-deserialized or
  post-serialized state.

  The implementation does not need to handle recursive composition/decomposition. This is handled
  by the object mapper.
  """

  @abc.abstractmethod
  def compose(self, data: t.Dict[str, t.Any]) -> t.Any: ...

  @abc.abstractmethod
  def decompose(self, obj: t.Any) -> t.Dict[str, t.Any]: ...
