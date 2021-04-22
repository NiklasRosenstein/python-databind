
import abc
import collections
import typing as t
from dataclasses import dataclass, field, Field as _Field
import nr.preconditions as preconditions
from .deser import IAnnotationsProvider, IDeserializer, IDeserializerProvider, ISerializer, ISerializerProvider, DeserializerNotFound, SerializerNotFound
from .settings import Settings
from .typehint import Concrete, TypeHint
from ..annotations import Annotation, get_annotation

T_Annotation = t.TypeVar('T_Annotation', bound=Annotation)



class IModule(IDeserializerProvider, ISerializerProvider):
  """
  Combines the #IDeserializerProvider and #ISerializerProvider interfaces.
  """

  @abc.abstractmethod
  def get_deserializer(self, type: TypeHint) -> IDeserializer:
    """ Can throw a #DeserializerNotFound exception. """

    pass

  @abc.abstractmethod
  def get_serializer(self, type: TypeHint) -> ISerializer:
    """ Can throw a #SerializerNotFound exception. """
    pass


class SimpleModule(IModule):
  """
  A module that you can register de-/serializers to and even other submodules. Only de-/serializers
  for concrete types can be registered in a #SimpleModule.
  """

  def __init__(self, name: str = None) -> None:
    self._name = name
    self._deserializers: t.Dict[type, IDeserializer] = {}
    self._serializers: t.Dict[type, ISerializer] = {}
    self._submodules: t.List[IModule] = []

  def __repr__(self):
    return f"<SimpleModule {self._name + ' ' if self._name else ''}at {hex(id(self))}>"

  def add_deserializer(self, type_: t.Type, deserializer: IDeserializer) -> None:
    preconditions.check_instance_of(type_, type)
    self._deserializers[type_] = deserializer

  def add_serializer(self, type_: t.Type, serializer: ISerializer) -> None:
    preconditions.check_instance_of(type_, type)
    self._serializers[type_] = serializer

  def add_submodule(self, module: IModule) -> None:
    preconditions.check_instance_of(module, IModule)
    self._submodules.append(module)

  # IModule
  def get_deserializer(self, type: TypeHint) -> IDeserializer:
    if isinstance(type, Concrete) and type.type in self._deserializers:
      return self._deserializers[type.type]
    for module in self._submodules:
      try:
        return module.get_deserializer(type)
      except DeserializerNotFound:
        pass  # intentional
    raise DeserializerNotFound(type)

  # IModule
  def get_serializer(self, type: TypeHint) -> ISerializer:
    if isinstance(type, Concrete) and type.type in self._serializers:
      return self._serializers[type.type]
    for module in self._submodules:
      try:
        return module.get_serializer(type)
      except SerializerNotFound:
        pass  # intentional
    raise SerializerNotFound(type)


class DefaultAnnotationsProvider(IAnnotationsProvider):
  """
  Default implementation for reading annotations annotated with #Annotation subclasses and from
  field annotations for #@dataclasses.dataclass decorated types.
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
    fields: t.Dict[str, _Field] = getattr(type, '__dataclass_fields__', {})
    field = fields.get(field_name)
    if not field:
      return None
    annotations = field.metadata.get('databind.core.annotations', [])
    return get_annotation(annotations, annotation_cls, None)


class AnnotationsRegistry(IAnnotationsProvider):
  """
  A registry for type annotations and type field annotations and additional annotation providers.
  Effectively this class allows to chain multiple annotation providers and manually override
  individual annotations.
  """

  @dataclass
  class _TypeOverrides:
    annotations: t.List[t.Any] = field(default_factory=list)
    fields: t.Dict[str, t.List[t.Any]] = field(default_factory=lambda: collections.defaultdict(list))

  def __init__(self) -> None:
    self._overrides: t.Dict[t.Type, AnnotationsRegistry._TypeOverrides] = collections.defaultdict(AnnotationsRegistry._TypeOverrides)
    self._subproviders: t.List[IAnnotationsProvider] = []

  def get_type_annotation(self,
      type: t.Type,
      annotation_cls: t.Type[T_Annotation]
  ) -> t.Optional[T_Annotation]:
    overrides = self._overrides.get(type)
    if overrides:
      return get_annotation(overrides.annotations, annotation_cls, None)
    for provider in self._subproviders:
      result = provider.get_type_annotation(type, annotation_cls)
      if result is not None:
        return result
    return None

  def get_field_annotation(self,
      type: t.Type,
      field_name: str,
      annotation_cls: t.Type[T_Annotation]
  ) -> t.Optional[T_Annotation]:
    overrides = self._overrides.get(type)
    if overrides:
      return get_annotation(overrides.fields.get(field_name, []), annotation_cls, None)
    for provider in self._subproviders:
      result = provider.get_field_annotation(type, field_name, annotation_cls)
      if result is not None:
        return result
    return None


class ObjectMapper(SimpleModule):
  """
  The #ObjectMapper is the entrypoint for de-/serializing data. It manages global annotations,
  such as styles, annotation overrides on types and fields, and modules that provide de-/serializers
  for the types that are encountered by the mapper.

  An empty mapper must first be initialized with at least one #Module.
  """
