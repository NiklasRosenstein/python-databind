
"""
Annotations in the context of the `databind.core` package provide information about a type or field
that changes the de-/serialization behaviour. Annotations can be attached directly to a type in one
of the following ways:

* directly annotate the type using Python decorator syntax
* pass the annotation along with the field description (see #databind.core.field())
* associate the annotation with a type or field in the #databind.core.ObjectMapper
"""

import typing as t

T = t.TypeVar('T')
T_Type = t.TypeVar('T_Type', bound=t.Type)
T_Annotation = t.TypeVar('T_Annotation', bound='Annotation')


class Annotation:
  """
  This is the abstract base class for annotations. Subclasses need not implement any particular
  methods, rather their behaviour is usually defined by their existence alone and any implementation
  supporting the particular annotation will need to check for the annotation's existence using the
  #get_annotation() function (usually through #IAnnotationsProvider.get_annotation()).

  Example:

  ```py
  from databind.core import Annotation, get_annotation
  from dataclasses import dataclass

  class MyAnnotation(Annotation):
    def __init__(self, message: str) -> None:
      self.message = message

  @dataclass
  @MyAnnotation('Hello, World!')
  class MyDataclass:
    # ...

  print(get_annotation(MyDataclass, MyAnnotation).message)  # Hello, World!
  ```
  """

  ANNOTATIONS_ATTRIBUTE_NAME = '__databind_annotations__'

  def __call__(self, cls: T_Type) -> T_Type:
    """
    Decorate a class with this annotation. Creates the `__databind_annotations__` attribute on the
    specified *cls* if it does not exist and registers the annotation *self* to it. The annotation
    can be retrieved again using the #get_annotation() method on *cls*.
    """

    if not isinstance(cls, type):
      raise TypeError(f'@{type(self).__name__}(...) should be used to annotated types only')

    if self.ANNOTATIONS_ATTRIBUTE_NAME not in vars(cls):
      setattr(cls, self.ANNOTATIONS_ATTRIBUTE_NAME, {})

    annotations: t.Dict = getattr(cls, self.ANNOTATIONS_ATTRIBUTE_NAME)
    annotations[type(self)] = self
    return cls


def get_annotation(
    source: t.Union[t.Type, t.Iterable[t.Any]],
    annotation_cls: t.Type[T_Annotation],
    default: T
) -> t.Union[T_Annotation, T]:
  """
  Get an instance of an annotation by the specified *annotation_cls* from the *source*, which must
  be either a type or a list of annotation objects. Returns the first annotation object where the
  type matches exactly the *annotation_cls* (subclasses are not returned).

  If no matching annotation object is found, the *default* value is returned.
  """

  if isinstance(source, type):
    return get_type_annotations(source).get(annotation_cls, default)

  if isinstance(source, t.Iterable):
    for item in source:
      if type(item) == annotation_cls:
        return item
    return default

  raise TypeError(f'expected type or Iterable, got {type(source).__name__!r} instead')


def get_type_annotations(source: t.Type) -> t.Dict[t.Type, t.Any]:
  return getattr(source, Annotation.ANNOTATIONS_ATTRIBUTE_NAME, {})


from .alias import alias
from .datefmt import datefmt
from .fieldinfo import fieldinfo
from .precision import precision
from .unionclass import unionclass
from .typeinfo import typeinfo

__all__ = [
  'Annotation',
  'get_annotation',
  'get_type_annotation',
  'alias',
  'datefmt',
  'fieldinfo',
  'precision',
  'unionclass',
  'typeinfo'
]
