
import abc
import dataclasses
import enum
import importlib
import pkg_resources
import types
import typing as t
import typing_extensions as te
import weakref

from nr.util.functional import assure
from nr.util.stream import Stream

from databind.core.annotations.base import Annotation, get_annotation
from databind.core.annotations.typeinfo import typeinfo
from .adapter import TypeContext, TypeHintAdapter, TypeHintAdapterError
from .schema import ObjectType
from .types import BaseType, ConcreteType
from .utils import type_repr

T_Type = t.TypeVar('T_Type', bound=t.Type)


@dataclasses.dataclass
class UnionTypeError(Exception):
  type: t.Union[str, t.Type, 'BaseType']
  subtypes: 'UnionSubtypes'

  def __str__(self) -> str:
    typ = self.type.__name__ if isinstance(self.type, type) else str(self.type)
    owner = self.subtypes.owner() if self.subtypes.owner else None
    if not owner or owner.name or not owner.python_type:
      return f'type `{typ}` is not a member of union `{owner.name if owner else "unknown"}`'
    else:
      owner_name = owner.python_type.__name__ if isinstance(owner.python_type, type) else str(owner.python_type)
      return f'type `{typ}` is not a member of @union `{owner_name}`'


class UnionSubtypes(abc.ABC):
  """
  This interface describes the subtypes of a union type.
  """

  owner: t.Optional['weakref.ReferenceType[UnionType]'] = None

  @abc.abstractmethod
  def get_type_name(self, type_: 'BaseType', type_hint_adapter: 'TypeHintAdapter') -> str:
    """
    Given a type that is a member of the union subtypes, return the name of the type
    that is used as a discriminator when serializing a value of the type. Raises a
    #UnionTypeError exception if *type* is not a member of this union subtypes.
    """

  @abc.abstractmethod
  def get_type_by_name(self, name: str, type_hint_adapter: 'TypeHintAdapter') -> 'BaseType':
    """
    Given the name of the type that is used as a discriminator value when deserializing
    a value, return the actual type behind that name in the union subtypes. If the name
    is not known, raise a #UnionTypeError.
    """

  @abc.abstractmethod
  def get_type_names(self) -> t.List[str]:
    """
    Return a list of the type names known to the union subtypes. This may not be possible
    to implement in all cases, so it may raise a #NotImplementedError in that case.
    """


class EntrypointSubtypes(UnionSubtypes):
  """
  Provides union subtypes per a Python entrypoint group.
  """

  def __init__(self, name: str) -> None:
    self._name = name
    self._entrypoints_cache: t.Optional[t.Dict[str, pkg_resources.EntryPoint]] = None

  def __repr__(self) -> str:
    return f'EntrypointSubtypes(name={self._name!r})'

  @property
  def _entrypoints(self) -> t.Dict[str, pkg_resources.EntryPoint]:
    if self._entrypoints_cache is None:
      self._entrypoints_cache = {}
      for ep in pkg_resources.iter_entry_points(self._name):
        self._entrypoints_cache[ep.name] = ep
    return self._entrypoints_cache

  def get_type_name(self, type_: 'BaseType', type_hint_adapter: 'TypeHintAdapter') -> str:
    subject_type: t.Optional[t.Type] = None
    if isinstance(type_, ConcreteType):
      subject_type = type_.type
    elif isinstance(type_, ObjectType):
      subject_type = type_.schema.python_type
    if subject_type is not None:
      for ep in self._entrypoints.values():
        if ep.load() == subject_type:
          return ep.name
    raise UnionTypeError(type_, self)

  def get_type_by_name(self, name: str, type_hint_adapter: 'TypeHintAdapter') -> 'BaseType':
    try:
      return TypeContext(type_hint_adapter).adapt_type_hint(self._entrypoints[name].load())
    except KeyError:
      raise UnionTypeError(name, self)

  def get_type_names(self) -> t.List[str]:
    return list(self._entrypoints.keys())


@dataclasses.dataclass
class DynamicSubtypes(UnionSubtypes):

  #: A #typing type hint, an actual type, a #BaseType or a callable that returns one of the aforementioned.
  _Type = t.Union[t.Any, t.Type, 'BaseType', t.Callable[[], t.Union[t.Any, t.Type, 'BaseType']]]
  _members: t.Dict[str, _Type]

  def __init__(self, members: t.Dict[str, _Type] = None) -> None:
    self._members = members or {}

  def __repr__(self) -> str:
    return f'DynamicSubtypes(members={self.get_type_names()})'

  def get_type_name(self, type_: 'BaseType', type_hint_adapter: 'TypeHintAdapter') -> str:
    if not isinstance(type_, BaseType):
      raise RuntimeError(f'expected BaseType, got {type(type_).__name__}')
    for key in self._members:
      value = self.get_type_by_name(key, type_hint_adapter)
      if value == type_:
        return key
    raise UnionTypeError(type_, self)

  def get_type_by_name(self, name: str, type_hint_adapter: 'TypeHintAdapter') -> 'BaseType':
    try:
      member = self._members[name]
    except KeyError:
      raise UnionTypeError(name, self)
    else:
      # Resolve the callable once.
      if isinstance(member, types.FunctionType):
        member = member()
      if not isinstance(member, BaseType):
        member = TypeContext(type_hint_adapter).adapt_type_hint(member)
      self._members[name] = member
      assert isinstance(member, BaseType), (member, type(member))
      return member

  def get_type_names(self) -> t.List[str]:
    return list(self._members.keys())

  def add_type(self, name: str, type_: _Type) -> None:
    if name in self._members:
      raise RuntimeError(f'type {name!r} already registered')
    self._members[name] = type_


class ChainSubtypes(UnionSubtypes):

  def __init__(self, *subtypes: UnionSubtypes) -> None:
    self._subtypes = subtypes

  def __repr__(self) -> str:
    return f'ChainSubtypes({", ".join(map(repr, self._subtypes))})'

  def get_type_name(self, type_: 'BaseType', type_hint_adapter: 'TypeHintAdapter') -> str:
    for subtypes in self._subtypes:
      try:
        return subtypes.get_type_name(type_, type_hint_adapter)
      except UnionTypeError:
        pass
    raise UnionTypeError(type_, self)

  def get_type_by_name(self, name: str, type_hint_adapter: 'TypeHintAdapter') -> 'BaseType':
    for subtypes in self._subtypes:
      try:
        return subtypes.get_type_by_name(name, type_hint_adapter)
      except UnionTypeError:
        pass
    raise UnionTypeError(name, self)

  def get_type_names(self) -> t.List[str]:
    def _gen() -> t.Iterator[str]:
      for subtypes in self._subtypes:
        try:
          yield from subtypes.get_type_names()
        except NotImplementedError:
          pass
    return Stream(_gen()).concat().distinct().collect()


class ImportSubtypes(UnionSubtypes):

  def __repr__(self) -> str:
    return 'ImportSubtypes()'

  def get_type_name(self, type_: 'BaseType', type_hint_adapter: 'TypeHintAdapter') -> str:
    type_name = f'{type_.__module__}.{type_.__qualname__}'  # type: ignore
    if '<' in type_.__qualname__:  # type: ignore
      raise ValueError(f'non-global type {type_name} is not addressible')
    return type_name

  def get_type_by_name(self, name: str, type_hint_adapter: 'TypeHintAdapter') -> 'BaseType':
    parts = name.split('.')
    offset = 1
    module_name = parts[0]
    module = importlib.import_module(module_name)

    # Import as many modules as we can.
    for offset, part in enumerate(parts[offset:], offset):
      sub_module_name = module_name + '.' + part
      try:
        module = importlib.import_module(sub_module_name)
        module_name = sub_module_name
      except ImportError as exc:
        if sub_module_name not in str(exc):
          raise
        #offset -= 1
        break

    # Read the class.
    target = module
    for offset, part in enumerate(parts[offset:], offset):
      target = getattr(target, part)

    if not isinstance(target, type):
      raise ValueError(f'{name!r} does not point to a type (got {type(target).__name__} instead)')

    return TypeContext(type_hint_adapter).adapt_type_hint(target)

  def get_type_names(self) -> t.List[str]:
    raise NotImplementedError


class UnionStyle(enum.Enum):
  """
  The styles in which unions can be de-/serialized. It is only relevant for union subtypes
  that contain multiple fields (such as #ObjectType).
  """

  #: In the nested style, the value of a union is saved on a different level
  #: than the discriminator key, avoiding any possible field name clashes with
  #: the union discriminator key (except if the type name conflicts with the
  #: discriminator key).
  nested = enum.auto()

  #: The flat style places the fields of a union value on the same level.
  flat = enum.auto()

  #: The "keyed" style expects a mapping with a single key that acts as the discriminator.
  keyed = enum.auto()


@dataclasses.dataclass
class UnionType(BaseType):
  """
  Represents a union of multiple types that is de-/serialized with a discriminator value.
  """

  DEFAULT_STYLE: t.ClassVar['UnionStyle'] = UnionStyle.nested
  DEFAULT_DISCRIMINATOR_KEY = 'type'

  subtypes: 'UnionSubtypes'
  style: t.Optional['UnionStyle'] = None
  discriminator_key: t.Optional[str] = None
  nesting_key: t.Optional[str] = None
  name: t.Optional[str] = None
  python_type: t.Optional[t.Any] = None  # Can be a Python type or an actual type hint
  annotations: t.List[t.Any] = dataclasses.field(default_factory=list)

  def __post_init__(self) -> None:
    if not self.name and self.python_type is None:
      raise ValueError(f'UnionType() requires either name or python_type')

  def __repr__(self) -> str:
    return f'UnionType({self.name or type_repr(self.python_type)})'

  def to_typing(self) -> t.Any:
    return self.python_type

  def visit(self, func: t.Callable[['BaseType'], 'BaseType']) -> 'BaseType':
    return func(self)


class _Subtypes:
  dynamic: te.Final = DynamicSubtypes
  entrypoint: te.Final = EntrypointSubtypes
  chain: te.Final = ChainSubtypes
  import_: te.Final = ImportSubtypes


@dataclasses.dataclass
class union(Annotation):
  """
  Used to annotate that a class describes a union.

  Note that if the decorated class provides properties that should be inherited by the child
  dataclasses, you need to also decorate the class as a `@dataclass`. In the natural scenario,
  a union class in itself is not constructible. If you wish to be able to create instances of
  the decorated class, set the `constructible` parameter to `True`.  If the parameter is not
  specified or set to `False`, the decorated classes' constructor will be replaced with
  #no_construct.

  Examples:

  ```py
  import abc
  import dataclasses
  from databind.core.annotations import union

  @union()
  @dataclasses.dataclass
  class Person:
    name: str

  @union.subtype(Person)
  @dataclasses.dataclass
  class Student(Person):
      courses: t.Set[str]

  @union(subtypes = union.Subtypes.entrypoint('my.entrypoint'))
  class IPlugin(abc.ABC):
    pass # ...
  ```
  """

  Subtypes: t.ClassVar = _Subtypes
  Style: t.ClassVar = UnionStyle

  subtypes: UnionSubtypes
  style: t.Optional[UnionStyle]
  discriminator_key: t.Optional[str]
  constructible: bool
  name: t.Optional[str]
  decorated_type: t.Optional[t.Type]

  def __init__(self,
    subtypes: t.Union[UnionSubtypes, t.Sequence[t.Type], t.Mapping[str, t.Type]] = None,
    *,
    style: t.Optional[UnionStyle] = None,
    discriminator_key: t.Optional[str] = None,
    nesting_key: t.Optional[str] = None,
    constructible: bool = False,
    name: str = None,
  ) -> None:

    self.subtypes = DynamicSubtypes()
    if isinstance(subtypes, UnionSubtypes):
      self.subtypes = subtypes
    elif isinstance(subtypes, t.Sequence):
      for typ in subtypes:
        self.subtypes.add_type(typeinfo.get_name(typ), typ)
    elif isinstance(subtypes, t.Mapping):
      for key, typ in subtypes.items():
        self.subtypes.add_type(key, typ)
    elif subtypes is not None:
      raise TypeError(f'bad subtypes argument: {subtypes!r}')

    self.style = style
    self.discriminator_key = discriminator_key
    self.nesting_key = nesting_key
    self.constructible = constructible
    self.name = name
    self.decorated_type = None

  def __hash__(self) -> int:
    # NOTE (@NiklasRosenstein): We make the class hashable to support use cases where it is used in `typing.Annotated`
    #   and that type hint is subsequently further combined into other types. The typing module expects arguments
    #   to annotated types to be hashable.
    return id(self)

  @staticmethod
  def subtype(extends: t.Type, name: str = None) -> t.Callable[[T_Type], T_Type]:
    """
    Decorator for subtypes of the #@union-decorated type *extends*. The *extends* class must
    use #union.Subtypes.Dynamic. If a *name* is specified, the class will also be decorated
    with the #typeinfo annotation.

    The decorated class _must_ be a subclass of the *extends* class, otherwise a #TypeError is
    raised.

    Example:

    ```py
    @dataclass
    @union.subtype(Person)
    class Student(Person):
      courses: t.Set[str]
    ```
    """

    assert isinstance(extends, type), extends
    inst = assure(get_annotation(extends, union, None), lambda: f'{extends.__name__} is not annotated with @union')
    assert isinstance(inst.subtypes, DynamicSubtypes), f'{extends.__name__} is not using union.Subtypes.Dynamic'
    subtypes = inst.subtypes

    def decorator(subtype: T_Type) -> T_Type:
      assert isinstance(subtype, type), subtype
      assert issubclass(subtype, extends), f'{subtype} is not a subclass of {extends}'
      if name is not None:
        subtype = typeinfo(name)(subtype)
      subtypes.add_type(typeinfo.get_name(subtype), subtype)
      return subtype
    return decorator

  @staticmethod
  def no_construct(self: t.Any) -> None:
    """
    This class is not constructible. Use any of it's subtypes.
    """

    raise TypeError(f'@union {type(self).__name__} is not constructible')

  # Annotation

  def __call__(self, cls: T_Type) -> T_Type:
    if not self.constructible:
      cls.__init__ = union.no_construct
    self.decorated_type = None
    return super().__call__(cls)


class UnionAdapter(TypeHintAdapter):
  """
  Adapter for classes decorated with #@union().
  """

  def adapt_type_hint(self, type_hint: t.Any, context: TypeContext) -> BaseType:
    if not isinstance(type_hint, BaseType):
      raise TypeHintAdapterError(self, str(type_hint))

    union_ann = get_annotation(type_hint.annotations, union, None)
    if union_ann is None and isinstance(type_hint, ConcreteType):
      union_ann = get_annotation(type_hint.type, union, None)
    elif union_ann is None and isinstance(type_hint, ObjectType):
      union_ann = type_hint.schema.union

    if union_ann:
      if union_ann.subtypes.owner:
        result_type = union_ann.subtypes.owner()
        if result_type:
          return result_type
      result_type = UnionType(
        union_ann.subtypes,
        union_ann.style,
        union_ann.discriminator_key,
        union_ann.nesting_key,
        union_ann.name,
        type_hint.to_typing())
      result_type.subtypes.owner = weakref.ref(result_type)
      return result_type

    return type_hint


unionclass = union  # Backwards compatibility <=1.0.1
