
import abc
import enum
import pkg_resources
import typing as t
import weakref
from dataclasses import dataclass
import nr.preconditions as preconditions
from . import Annotation, get_annotation
from .typeinfo import typeinfo


T_Type = t.TypeVar('T_Type', bound=t.Type)


@dataclass
class UnionTypeError(Exception):
  type: t.Union[str, t.Type]
  subtypes: '_ISubtypes'

  def __str__(self) -> str:
    owner = self.subtypes.owner() if self.subtypes.owner else None
    typ = self.type.__name__ if isinstance(self.type, type) else str(self.type)
    return f'type `{typ}` is not a member of @unionclass `{owner.__name__ if owner else "<unknown>"}`'


class _ISubtypes(metaclass=abc.ABCMeta):
  # @:change-id unionclass.ISubtypes

  owner: t.Optional['weakref.ref[t.Type]']

  @abc.abstractmethod
  def get_type_name(self, type: t.Type) -> str: ...

  @abc.abstractmethod
  def get_type_by_name(self, name: str) -> t.Type: ...

  @abc.abstractmethod
  def get_type_names(self) -> t.List[str]: ...  # raises NotImplementedError


class _SubtypesEnum(enum.Enum):
  dynamic = enum.auto()


class _Entrypoint(t.NamedTuple):
  # @:change-id _Subtypes.Entrypoint

  name: str


class _Subtypes:
  # @:change-id unionclass.Subtypes

  dynamic = _SubtypesEnum.dynamic
  entrypoint = _Entrypoint


U_Subtypes = t.Union[
  _SubtypesEnum,
  _Entrypoint,
  _ISubtypes,
  t.Sequence[t.Type],
  t.Mapping[str, t.Type]]


class Style(enum.Enum):
  nested = enum.auto()
  flat = enum.auto()


@dataclass
class unionclass(Annotation):
  # @:change-id !databind.core.unionclass
  """
  Used to annotate that a class describes a union.

  Note that if the decorated class provides properties that should be inherited by the child
  dataclasses, you need to also decorate the class as a `@dataclass`. In the natural scenario,
  a union class in itself is not constructible. If you wish to be able to create instances of
  the decorated class, set the `constructible` parameter to `True`.  If the parameter is not
  specified or set to `False`, the decorated classes' constructor will be replaced with
  #no_construct.

  Example:

  ```py
  from databind.core import unionclass

  @unionclass(subtypes = unionclass.Subtypes.Dynamic, constructible = True)
  @dataclass
  class Person:
    name: str

  Person('John Doe')  # works!
  ```
  """

  DEFAULT_STYLE = Style.nested
  DEFAULT_DISCRIMINATOR_KEY = 'type'

  subtypes: _ISubtypes
  constructible: bool
  style: t.Optional[Style]
  discriminator_key: t.Optional[str]

  def __init__(self, *,
    subtypes: U_Subtypes,
    constructible: bool = False,
    style: t.Optional[Style] = None,
    discriminator_key: t.Optional[str] = None
  ) -> None:
    """
    Create a union class decorator.

    The *subtypes* may be one of the following:

    * #unionclass.Subtypes.Dynamic
    * #unionclass.Subtypes.Entrypoint()
    * #unionclass.ISubtypes implementation
    * A dictionary of type names mapping to type objects
    """

    if isinstance(subtypes, _ISubtypes):
      self.subtypes = subtypes
    elif isinstance(subtypes, _Entrypoint):
      self.subtypes = _EntrypointSubtypes(subtypes.name)
    elif subtypes == _SubtypesEnum.dynamic:
      self.subtypes = _DynamicSubtypes()
    elif isinstance(subtypes, t.Sequence):
      self.subtypes = _DynamicSubtypes()
      for typ in subtypes:
        self.subtypes.add_type(typeinfo.get_name(typ), typ)
    elif isinstance(subtypes, t.Mapping):
      self.subtypes = _DynamicSubtypes()
      for key, typ in subtypes.items():
        self.subtypes.add_type(key, typ)
    else:
      raise TypeError(f'bad subtypes argument: {subtypes!r}')

    self.constructible = constructible
    self.style = style
    self.discriminator_key = discriminator_key

  @staticmethod
  def subtype(extends: t.Type, name: str = None) -> t.Callable[[T_Type], T_Type]:
    """
    Decorator for subtypes of the #@unionclass-decorated type *extends*. The *extends* class must
    use #unionclass.Subtypes.Dynamic. If a *name* is specified, the class will also be decorated
    with the #typeinfo annotation.

    The decorated class _must_ be a subclass of the *extends* class, otherwise a #TypeError is
    raised.

    Example:

    ```py
    @dataclass
    @unionclass.subtype(Person)
    class Student(Person):
      courses: t.Set[str]
    ```
    """

    preconditions.check_instance_of(extends, type)
    inst = preconditions.check_not_none(get_annotation(extends, unionclass, None),
      lambda: f'{extends.__name__} is not annotated with @unionclass')
    subtypes = preconditions.check_instance_of(inst.subtypes, _DynamicSubtypes,
      lambda: f'{extends.__name__} is not using unionclass.Subtypes.Dynamic')
    def decorator(subtype: T_Type) -> T_Type:
      preconditions.check_subclass_of(subtype, extends)
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

    raise TypeError(f'@unionclass {type(self).__name__} is not constructible')

  def with_fallback(self, other: t.Optional['unionclass']) -> 'unionclass':
    return unionclass(
      subtypes=self.subtypes,
      constructible=self.constructible,
      style=self.style or (other.style if other else None) or self.DEFAULT_STYLE,
      discriminator_key=self.discriminator_key or (other.discriminator_key if other else None)
        or self.DEFAULT_DISCRIMINATOR_KEY)

  # Annotation

  def __call__(self, cls: T_Type) -> T_Type:
    if not self.constructible:
      cls.__init__ = unionclass.no_construct
    self.subtypes.owner = weakref.ref(cls)
    return super().__call__(cls)

  Subtypes = _Subtypes
  ISubtypes = _ISubtypes
  UnionTypeError = UnionTypeError
  Style = Style


class _EntrypointSubtypes(_ISubtypes):

  def __init__(self, name: str) -> None:
    self._name = name
    self._entrypoints_cache: t.Optional[t.Dict[str, pkg_resources.EntryPoint]] = None

  def __repr__(self) -> str:
    return f'_EntrypointSubtypes(name={self._name!r})'

  @property
  def _entrypoints(self) -> t.Dict[str, pkg_resources.EntryPoint]:
    if self._entrypoints_cache is None:
      self._entrypoints_cache = {}
      for ep in pkg_resources.iter_entry_points(self._name):
        self._entrypoints_cache[ep.name] = ep
    return self._entrypoints_cache

  def get_type_name(self, type: t.Type) -> str:
    for ep in self._entrypoints.values():
      if ep.load() == type:
        return ep.name
    raise UnionTypeError(type, self)

  def get_type_by_name(self, name: str) -> t.Type:
    try:
      return self._entrypoints[name].load()
    except KeyError:
      raise UnionTypeError(name, self)

  def get_type_names(self) -> t.List[str]:
    return list(self._entrypoints.keys())


class _DynamicSubtypes(_ISubtypes):

  def __init__(self) -> None:
    self._members: t.Dict[str, t.Type] = {}

  def __repr__(self) -> str:
    return f'_DynamicSubtypes(members={self.get_type_names()})'

  def get_type_name(self, type: t.Type) -> str:
    for key, value in self._members.items():
      if value == type:
        return key
    raise UnionTypeError(type, self)

  def get_type_by_name(self, name: str) -> t.Type:
    try:
      return self._members[name]
    except KeyError:
      raise UnionTypeError(name, self)

  def get_type_names(self) -> t.List[str]:
    return list(self._members.keys())

  def add_type(self, name: str, type: t.Type) -> None:
    if name in self._members:
      raise RuntimeError(f'type {name!r} already registered')
    self._members[name] = type
