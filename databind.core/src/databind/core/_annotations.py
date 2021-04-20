
"""
Base class for annotations.
"""

import typing as t
from ._datamodel import FieldMetadata

T = t.TypeVar('T')
T_Type = t.TypeVar('T_Type', bound=t.Type)
T_Annotation = t.TypeVar('T_Annotation', bound='Annotation')


class Annotation:
  """
  Base class for annotations. Instances of annotations can be passed into the #field() function or
  to decorate #datamodel() class definitions.
  """

  ANNOTATIONS_ATTRIBUTE_NAME = '__databind_annotations__'

  def __call__(self, cls: T_Type) -> T_Type:
    """
    Decorate a class with this annotation. This will append the annotation to the
    `__databind_annotations__` member of the class.
    """

    if not isinstance(cls, type):
      raise TypeError(f'@{type(self).__name__}(...) should be used to annotated types only')

    if self.ANNOTATIONS_ATTRIBUTE_NAME not in vars(cls):
      setattr(cls, self.ANNOTATIONS_ATTRIBUTE_NAME, {})

    annotations: t.Dict = getattr(cls, self.ANNOTATIONS_ATTRIBUTE_NAME)
    annotations[type(self)] = self
    return cls


def get_annotation(
    source: t.Union[t.Type, FieldMetadata], annotation_cls: t.Type[T_Annotation],
    default: T = None
) -> t.Union[T_Annotation, T]:
  """
  Retrieve the first instance of the specified #Annotation subclass in the *source*, or return the
  *default*. The annotation class is matched exactly, inheritance is not supported.
  """

  if isinstance(source, FieldMetadata):
    for item in source.annotations:
      if type(item) == annotation_cls:
        return item
    return default

  if isinstance(source, type):
    return getattr(source, Annotation.ANNOTATIONS_ATTRIBUTE_NAME, {}).get(annotation_cls, default)

  raise TypeError(f'expected FieldMetadata or type, got {type(source).__name__!r} instead')
