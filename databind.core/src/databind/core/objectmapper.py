
import abc
import collections
import typing as t
from dataclasses import dataclass, field, Field as _Field
from functools import reduce
import nr.preconditions as preconditions
from . import typehint
from .api import IAnnotationsProvider, IDeserializer, IDeserializerProvider, ISerializer, \
  ISerializerProvider, DeserializationError, DeserializerNotFound, SerializationError, \
  SerializerNotFound, ITypeHintAdapter
from .annotations import Annotation, get_annotation
from .location import Location
from .settings import Settings
from .typehint import Concrete, TypeHint

__all__ = [
  'IModule',
  'SimpleModule',
  'ObjectMapper',
]


T_Annotation = t.TypeVar('T_Annotation', bound=Annotation)


class IModule(IDeserializerProvider, ISerializerProvider, ITypeHintAdapter):
  """
  Combination of various interfaces, with default implementations acting as a no-op.
  """

  def get_deserializer(self, type: TypeHint) -> IDeserializer:
    raise DeserializerNotFound(type)

  def get_serializer(self, type: TypeHint) -> ISerializer:
    raise SerializerNotFound(type)

  def adapt_type_hint(self, type: TypeHint) -> TypeHint:
    return type


class SimpleModule(IModule):
  """
  A module that you can register de-/serializers to and even other submodules. Only de-/serializers
  for concrete types can be registered in a #SimpleModule. Submodules are tested in the reversed
  order that they were registered.
  """

  def __init__(self, name: str = None) -> None:
    self.__name = name
    self.__deserializers: t.Dict[type, IDeserializer] = {}
    self.__serializers: t.Dict[type, ISerializer] = {}
    self.__type_hint_adapters: t.List[ITypeHintAdapter] = []
    self.__submodules: t.List[IModule] = []

  def __repr__(self):
    return f"<SimpleModule {self.__name + ' ' if self.__name else ''}at {hex(id(self))}>"

  def add_deserializer(self, type_: t.Type, deserializer: IDeserializer) -> None:
    preconditions.check_instance_of(type_, type)
    self.__deserializers[type_] = deserializer

  def add_serializer(self, type_: t.Type, serializer: ISerializer) -> None:
    preconditions.check_instance_of(type_, type)
    self.__serializers[type_] = serializer

  def add_type_hint_adapter(self, adapter: ITypeHintAdapter) -> None:
    preconditions.check_instance_of(adapter, ITypeHintAdapter)
    self.__type_hint_adapters.append(adapter)

  def add_module(self, module: IModule) -> None:
    preconditions.check_instance_of(module, IModule)
    self.__submodules.append(module)

  # IModule
  def get_deserializer(self, type: TypeHint) -> IDeserializer:
    if isinstance(type, Concrete) and type.type in self.__deserializers:
      return self.__deserializers[type.type]
    for module in reversed(self.__submodules):
      try:
        return module.get_deserializer(type)
      except DeserializerNotFound:
        pass  # intentional
    raise DeserializerNotFound(type)

  # IModule
  def get_serializer(self, type: TypeHint) -> ISerializer:
    if isinstance(type, Concrete) and type.type in self.__serializers:
      return self.__serializers[type.type]
    for module in reversed(self.__submodules):
      try:
        return module.get_serializer(type)
      except SerializerNotFound:
        pass  # intentional
    raise SerializerNotFound(type)

  # IModule
  def adapt_type_hint(self, type_: TypeHint) -> TypeHint:
    type_ = reduce(lambda t, a: a.adapt_type_hint(t), self.__type_hint_adapters, type_)
    type_ = reduce(lambda t, m: m.adapt_type_hint(m), self.__submodules, type_)
    return type_


class DefaultAnnotationsProvider(IAnnotationsProvider):
  """
  Default implementation for reading #Annotation#s from types, and for the fields of types
  decorated with #@dataclasses.dataclass. Field annotations are read from the field metadata
  directly (if attached to the `databind.core.annotations` key) and secondary from the
  `_annotations` class on the MRO.
  """

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

    # Look for annoations on the metadata of the dataclass fields.
    fields: t.Dict[str, _Field] = getattr(type, '__dataclass_fields__', {})
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
        meta_cls: t.Type = curr_type._annotations
        annotations = getattr(meta_cls, field_name, [])
        if isinstance(annotations, Annotation):
          ann = annotations
        else:
          ann = get_annotation(annotations, annotation_cls, None)
        if ann is not None:
          break

    return ann


class AnnotationsRegistry(IAnnotationsProvider):
  """
  A registry for type annotations and type field annotations and additional annotation providers.
  Effectively this class allows to chain multiple annotation providers and manually override
  individual annotations. Subproviders are tested in the reverse order that they were added.
  """

  @dataclass
  class _TypeOverrides:
    annotations: t.List[t.Any] = field(default_factory=list)
    fields: t.Dict[str, t.List[t.Any]] = field(default_factory=lambda: collections.defaultdict(list))

  def __init__(self) -> None:
    self.__overrides: t.Dict[t.Type, AnnotationsRegistry._TypeOverrides] = collections.defaultdict(AnnotationsRegistry._TypeOverrides)
    self.__subproviders: t.List[IAnnotationsProvider] = []

  def add_annotations_provider(self, provider: IAnnotationsProvider) -> None:
    self.__subproviders.append(provider)

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
      return get_annotation(overrides.fields.get(field_name, []), annotation_cls, None)
    for provider in reversed(self.__subproviders):
      result = provider.get_field_annotation(type, field_name, annotation_cls)
      if result is not None:
        return result
    return None


class ObjectMapper(SimpleModule, AnnotationsRegistry):

  def __init__(self, *modules: IModule, name: str = None):
    SimpleModule.__init__(self, name)
    AnnotationsRegistry.__init__(self)
    [self.add_module(m) for m in modules]
    self.add_annotations_provider(DefaultAnnotationsProvider())
    self.settings = Settings()
