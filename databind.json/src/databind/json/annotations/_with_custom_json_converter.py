
import typing as t
from dataclasses import dataclass
from databind.core.mapper.converter import Context, ConversionNotApplicable, Converter, ConverterNotFound, ConverterProvider, Direction
from databind.core.annotations.base import Annotation, get_annotation
from databind.core.types.schema import ObjectType
from databind.core.types.types import BaseType, ConcreteType


@dataclass
class with_custom_json_converter(Annotation):
  """
  An annotation for a type to specify function(s) for custom JSON de/serialization of the type.

  Note: This currently only works on dataclasses.

  Example:

  ```py
  import typing as t
  import dataclasses
  from databind.core.mapper.converter import Context
  from databind.json.annotations import with_custom_json_converter

  @with_custom_json_converter()
  @dataclasses.dataclass
  class FieldConfig:
    type: str
    docs: str | None

    @classmethod
    def _convert_json(cls, ctx: 'Context') -> t.Any:
      if ctx.direction.is_deserialize() and isinstance(ctx.value, str):
        return cls(ctx.value, None)
      return NotImplemented
  ```
  """

  #: The custom converter, or the name of a classmethod on the type that will be called to do the conversion.
  #: If a method name on the class is used, the method may return #NotImplemented to fall back to the default
  #: behaviour.
  converter: t.Union[Converter, str] = '_convert_json'

  @staticmethod
  def apply_converter(python_type: t.Type, ctx: 'Context') -> t.Any:
    custom = get_annotation(python_type, with_custom_json_converter, None)
    if not custom:
      raise ConversionNotApplicable()

    if isinstance(custom.converter, str):
      result = getattr(python_type, custom.converter)(ctx)
      if result is NotImplemented:
        raise ConversionNotApplicable()
      return result

    return custom.converter.convert(ctx)
