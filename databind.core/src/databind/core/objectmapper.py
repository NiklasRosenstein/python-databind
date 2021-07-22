
import collections
import typing as t
from dataclasses import dataclass, field, Field as _Field
from functools import reduce
from databind.core.schema import Field
import nr.preconditions as preconditions
from .api import (Context, ConverterNotFound, Direction, IAnnotationsProvider, IConverter,
  IConverterProvider, IObjectMapper, ITypeHintAdapter, Context)
from .annotations import Annotation, get_annotation
from .location import Location, Position
from .settings import Settings
from .types import ConcreteType, BaseType, from_typing

__all__ = [
  'IModule',
  'SimpleModule',
  'ObjectMapper',
]

T = t.TypeVar('T')
T_Annotation = t.TypeVar('T_Annotation', bound=Annotation)


class Module(IConverterProvider, ITypeHintAdapter):
  """
  Combination of various interfaces, with default implementations acting as a no-op.
  """

  def get_converter(self, type_: BaseType, direction: 'Direction') -> IConverter:
    raise ConverterNotFound(type_, direction)

  def adapt_type_hint(self, type_: BaseType, adapter: t.Optional[ITypeHintAdapter] = None) -> BaseType:
    return type_


class SimpleModule(Module):
  """
  A module that you can register de-/serializers to and even other submodules. Only de-/serializers
  for concrete types can be registered in a #SimpleModule. Submodules are tested in the reversed
  order that they were registered.
  """

  def __init__(self, name: str = None) -> None:
    self.__name = name
    self.__converters_by_type: t.Dict[Direction, t.Dict[t.Type, IConverter]] = {
      Direction.deserialize: {}, Direction.serialize: {}}
    self.__converter_providers: t.List[IConverterProvider] = []
    self.__type_hint_adapters: t.List[ITypeHintAdapter] = []

  def __repr__(self):
    return f"<{type(self).__name__} {self.__name + ' ' if self.__name else ''}at {hex(id(self))}>"

  def add_converter_provider(self, provider: IConverterProvider) -> None:
    preconditions.check_instance_of(provider, IConverterProvider)  # type: ignore
    self.__converter_providers.append(provider)

  def add_converter_for_type(self, type_: t.Type, converter: IConverter, direction: Direction = None) -> None:
    preconditions.check_instance_of(type_, type)
    preconditions.check_instance_of(converter, IConverter)  # type: ignore
    if direction is not None:
      preconditions.check_instance_of(direction, Direction)
      self.__converters_by_type[direction][type_] = converter
    else:
      self.__converters_by_type[Direction.deserialize][type_] = converter
      self.__converters_by_type[Direction.serialize][type_] = converter

  def add_type_hint_adapter(self, adapter: ITypeHintAdapter) -> None:
    preconditions.check_instance_of(adapter, ITypeHintAdapter)  # type: ignore
    self.__type_hint_adapters.append(adapter)

  def add_module(self, module: Module) -> None:
    preconditions.check_instance_of(module, Module)
    self.__converter_providers.append(module)
    self.__type_hint_adapters.append(module)

  def get_converter(self, type_: BaseType, direction: Direction) -> IConverter:
    preconditions.check_instance_of(type_, BaseType)  # type: ignore
    if isinstance(type_, ConcreteType) and type_.type in self.__converters_by_type[direction]:
      return self.__converters_by_type[direction][type_.type]
    elif type(type_) in self.__converters_by_type[direction]:
      return self.__converters_by_type[direction][type(type_)]
    for module in reversed(self.__converter_providers):
      try:
        return module.get_converter(type_, direction)
      except ConverterNotFound:
        pass  # intentional
    raise ConverterNotFound(type_, direction)

  def adapt_type_hint(self, type_: BaseType, adapter: ITypeHintAdapter = None) -> BaseType:
    return reduce(lambda t, a: a.adapt_type_hint(t, adapter), self.__type_hint_adapters, type_)


class DefaultAnnotationsProvider(IAnnotationsProvider):
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
        meta_cls: t.Type = curr_type._annotations  # type: ignore
        annotations = getattr(meta_cls, field_name, [])
        if isinstance(annotations, Annotation):
          ann = t.cast(T_Annotation, annotations)
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
    self.__global_annotations: t.List[t.Any] = []

  def add_global_annotation(self, annotation: t.Any) -> None:
    self.__global_annotations.append(annotation)

  def add_annotations_provider(self, provider: IAnnotationsProvider) -> None:
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
      return get_annotation(overrides.fields.get(field_name, []), annotation_cls, None)
    for provider in reversed(self.__subproviders):
      result = provider.get_field_annotation(type, field_name, annotation_cls)
      if result is not None:
        return result
    return None


class ObjectMapper(IObjectMapper, SimpleModule, AnnotationsRegistry):

  def __init__(self, *modules: Module, name: str = None):
    SimpleModule.__init__(self, name)
    AnnotationsRegistry.__init__(self)
    self.settings = Settings()
    for module in modules:
      self.add_module(module)

  # IModule
  def adapt_type_hint(self, type_: BaseType, adapter: t.Optional[ITypeHintAdapter] = None) -> BaseType:

    if isinstance(type_, ConcreteType):
      # Type's for which we have a serializer or deserializer do not require adaptation.
      # The background here is that there can be #ConcreteType's that wrap a @dataclass
      # which would be adapter to an #ObjectType by the #DataclassAdapter unless we catch
      # that there is an explicit converter registered to handle that special case.
      has_converter = False
      try: self.get_converter(type_, Direction.deserialize)
      except ConverterNotFound: pass
      else: has_converter = True
      if not has_converter:
        try: self.get_converter(type_, Direction.serialize)
        except ConverterNotFound: pass
        else: has_converter = True
        pass

      if has_converter:
        return type_

    # Apply the type adaptation recursively on all nested types.
    parent_method = super().adapt_type_hint
    def visitor(current_type: BaseType) -> BaseType:
      return parent_method(current_type, adapter or self)
    return type_.visit(visitor)

  @classmethod
  def default(cls, *modules: Module, name: str = None) -> 'ObjectMapper':
    from .default.dataclasses import DataclassAdapter
    from .default.unionclass import UnionclassAdapter
    mapper = cls(UnionclassAdapter(), DataclassAdapter(), *modules, name=name)
    mapper.add_annotations_provider(DefaultAnnotationsProvider())
    return mapper

  def convert(self,
    direction: Direction,
    value: t.Any,
    type_hint: t.Union[BaseType, t.Type[T]],
    filename: t.Optional[str] = None,
    position: t.Optional[Position] = None,
    key: t.Union[str, int, None] = None,
    annotations: t.Optional[t.List[t.Any]] = None,
    settings: t.Optional[t.List[t.Any]] = None,
  ) -> T:
    preconditions.check_instance_of(direction, Direction)
    if isinstance(type_hint, BaseType):
      th = type_hint
    else:
      th = self.adapt_type_hint(from_typing(type_hint).normalize()).normalize()
    field = Field('$', th, annotations or [])
    loc = Location(None, th, key, filename, position)
    ctx = Context(None, self, Settings(*(settings or []), parent=self.settings), direction, value, loc, field)
    return ctx.convert()

  def deserialize(self,
    value: t.Any,
    type_hint: t.Union[BaseType, t.Type[T]],
    filename: str = None,
    pos: Position = None,
    key: t.Union[str, int] = None,
    annotations: t.List[t.Any] = None,
    settings: t.Optional[t.List[t.Any]] = None,
  ) -> T:
    return self.convert(Direction.deserialize, value, type_hint, filename, pos, key, annotations, settings)

  def serialize(self,
    value: t.Any,
    type_hint: t.Union[BaseType, t.Type[T]],
    filename: str = None,
    pos: Position = None,
    key: t.Union[str, int] = None,
    annotations: t.List[t.Any] = None,
    settings: t.Optional[t.List[t.Any]] = None,
  ) -> t.Any:
    return self.convert(Direction.serialize, value, type_hint, filename, pos, key, annotations, settings)
