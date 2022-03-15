
import abc
import collections
import dataclasses
import enum
import typing as t
import typing_extensions as te
import weakref

from databind.core.types.utils import get_type_hints, unpack_type_hint

T = t.TypeVar('T')
U = t.TypeVar('U')
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

  owner: t.Optional['weakref.ReferenceType[t.Type]'] = None

  def __call__(self, cls: T_Type) -> T_Type:
    """
    Decorate a class with this annotation. Creates the `__databind_annotations__` attribute on the
    specified *cls* if it does not exist and registers the annotation *self* to it. The annotation
    can be retrieved again using the #get_annotation() method on *cls*.
    """

    if self.owner is not None:
      raise RuntimeError('annotation is already attached to a type')

    if not isinstance(cls, type):
      raise TypeError(f'@{type(self).__name__}(...) should be used to annotated types only')

    if self.ANNOTATIONS_ATTRIBUTE_NAME not in vars(cls):
      setattr(cls, self.ANNOTATIONS_ATTRIBUTE_NAME, {})

    annotations: t.Dict = getattr(cls, self.ANNOTATIONS_ATTRIBUTE_NAME)
    annotations[type(self)] = self
    self.owner = weakref.ref(cls)
    return cls


def get_annotation(
  source: t.Union[t.Type, t.Iterable[t.Any]],
  annotation_cls: t.Type[T],
  default: U,
) -> t.Union[T, U]:
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
  return vars(source).get(Annotation.ANNOTATIONS_ATTRIBUTE_NAME, {})


class AnnotationsProvider(metaclass=abc.ABCMeta):
  """
  Interface to provide annotations for a given type or field in a type.
  """

  @abc.abstractmethod
  def get_global_annotation(self, annotation_cls: t.Type[T_Annotation]) -> t.Optional[T_Annotation]:
    ...

  @abc.abstractmethod
  def get_type_annotation(self,
      type: t.Type,
      annotation_cls: t.Type[T_Annotation]
  ) -> t.Optional[T_Annotation]:
    ...

  @abc.abstractmethod
  def get_field_annotation(self,
      type: t.Type,
      field_name: str,
      annotation_cls: t.Type[T_Annotation]
  ) -> t.Optional[T_Annotation]:
    ...


class AnnotationsRegistry(AnnotationsProvider):
  """
  A registry for type annotations and type field annotations and additional annotation providers.
  Effectively this class allows to chain multiple annotation providers and manually override
  individual annotations. Subproviders are tested in the reverse order that they were added.
  """

  @dataclasses.dataclass
  class _TypeOverrides:
    annotations: t.List[t.Any] = dataclasses.field(default_factory=list)
    fields: t.Dict[str, t.List[t.Any]] = dataclasses.field(default_factory=lambda: collections.defaultdict(list))

  def __init__(self) -> None:
    self.__overrides: t.Dict[t.Type, AnnotationsRegistry._TypeOverrides] = collections.defaultdict(AnnotationsRegistry._TypeOverrides)
    self.__subproviders: t.List[AnnotationsProvider] = []
    self.__global_annotations: t.List[t.Any] = []

  def add_global_annotation(self, annotation: t.Any) -> None:
    self.__global_annotations.append(annotation)

  def add_type_annotation(self, type_: t.Type, annotation: t.Any) -> None:
    self.__overrides.setdefault(type_, self._TypeOverrides()).annotations.append(annotation)

  def add_field_annotation(self, type_: t.Type, field: str, annotation: t.Any) -> None:
    self.__overrides.setdefault(type_, self._TypeOverrides()).fields.setdefault(field, []).append(annotation)

  def add_annotations_provider(self, provider: AnnotationsProvider) -> None:
    self.__subproviders.append(provider)

  # IAnnotationsProvider
  def get_global_annotation(self, annotation_cls: t.Type[T_Annotation]) -> t.Optional[T_Annotation]:
    return get_annotation(self.__global_annotations, annotation_cls, None)

  # IAnnotationsProvider
  def get_type_annotation(self,
      type: t.Type,
      annotation_cls: t.Type[T_Annotation]
  ) -> t.Optional[T_Annotation]:
    overrides = self.__overrides.get(type)
    if overrides:
      return get_annotation(overrides.annotations, annotation_cls, None)
    for provider in reversed(self.__subproviders):
      result = provider.get_type_annotation(type, annotation_cls)
      if result is not None:
        return result
    return None

  # IAnnotationsProvider
  def get_field_annotation(self,
      type: t.Type,
      field_name: str,
      annotation_cls: t.Type[T_Annotation]
  ) -> t.Optional[T_Annotation]:
    overrides = self.__overrides.get(type)
    if overrides:
      annotation = get_annotation(overrides.fields.get(field_name, []), annotation_cls, None)
      if annotation is not None:
        return annotation
    for provider in reversed(self.__subproviders):
      result = provider.get_field_annotation(type, field_name, annotation_cls)
      if result is not None:
        return result
    return None


class DefaultAnnotationsProvider(AnnotationsProvider):
  """
  Default implementation for reading #Annotation#s from types, and for the fields of types
  decorated with #@dataclasses.dataclass. Field annotations are read from the field metadata
  directly (if attached to the `databind.core.annotations` key) and secondary from the
  `_annotations` class on the MRO.
  """

  def get_global_annotation(self, annotation_cls: t.Type[T_Annotation]) -> t.Optional[T_Annotation]:
    return None

  def get_type_annotation(self,
      type: t.Type,
      annotation_cls: t.Type[T_Annotation]
  ) -> t.Optional[T_Annotation]:
    return get_annotation(type, annotation_cls, None)

  def get_field_annotation(self,
      type: t.Type,
      field_name: str,
      annotation_cls: t.Type[T_Annotation]
  ) -> t.Optional[T_Annotation]:

    # Support te.Annotated on enum values.
    if issubclass(type, enum.Enum):
      ann = get_type_hints(type).get(field_name)
      generic, args = unpack_type_hint(ann)
      if generic == te.Annotated:
        return get_annotation(args[1:], annotation_cls, None)

    # Look for annotations on the metadata of the dataclass fields.
    fields: t.Dict[str, dataclasses.Field] = getattr(type, '__dataclass_fields__', {})
    field = fields.get(field_name)
    if not field:
      return None

    annotations = field.metadata.get('databind.core.annotations', [])
    ann = get_annotation(annotations, annotation_cls, None)
    if ann is not None:
      return ann

    # Search for annotations of the field in the `_annotations` class.
    for curr_type in type.__mro__:
      if hasattr(curr_type, '_annotations'):
        meta_cls: t.Type = curr_type._annotations  # type: ignore
        annotations = getattr(meta_cls, field_name, [])
        if isinstance(annotations, Annotation):
          ann = t.cast(T_Annotation, annotations)
        else:
          ann = get_annotation(annotations, annotation_cls, None)
        if ann is not None:
          break

    return ann
