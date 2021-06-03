
import abc
import enum
import pkg_resources
import typing as t
from dataclasses import dataclass
import nr.preconditions as preconditions
from . import Annotation, get_annotation
from .typeinfo import typeinfo


T_Type = t.TypeVar('T_Type', bound=t.Type)


@dataclass
class UnionTypeError(Exception):
  type: t.Union[str, t.Type]
  subtypes: '_ISubtypes'


class _ISubtypes(metaclass=abc.ABCMeta):
  # @:change-id unionclass.ISubtypes

  @abc.abstractmethod
  def get_type_name(self, type: t.Type) -> str: ...

  @abc.abstractmethod
  def get_type_by_name(self, name: str) -> t.Type: ...

  @abc.abstractmethod
  def get_type_names(self) -> t.List[str]: ...  # raises NotImplementedError


class _SubtypesEnum(enum.Enum):
  DYNAMIC = enum.auto()


class _Entrypoint(t.NamedTuple):
  # @:change-id _Subtypes.ENTRYPOINT

  name: str


class _Subtypes:
  # @:change-id unionclass.Subtypes

  DYNAMIC = _SubtypesEnum.DYNAMIC
  ENTRYPOINT = _Entrypoint


U_Subtypes = t.Union[
  _SubtypesEnum,
  _Entrypoint,
  _ISubtypes,
  t.List[t.Type]]


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

  @unionclass(subtypes = unionclass.Subtypes.DYNAMIC, constructible = True)
  @dataclass
  class Person:
    name: str

  Person('John Doe')  # works!
  ```
  """

  Subtypes = _Subtypes
  ISubtypes = _ISubtypes
  UnionTypeError = UnionTypeError

  subtypes: _ISubtypes
  constructible: bool

  def __init__(self, *, subtypes: U_Subtypes, constructible: bool = False) -> None:
    """
    Create a union class decorator.

    The *subtypes* may be one of the following:

    * #unionclass.Subtypes.DYNAMIC
    * #unionclass.Subtypes.ENTRYPOINT()
    * #unionclass.ISubtypes implementation
    * A list of types
    """

    if isinstance(subtypes, _ISubtypes):
      self.subtypes = subtypes
    elif isinstance(subtypes, _Entrypoint):
      self.subtypes = _EntrypointSubtypes(subtypes.name)
    elif subtypes == _SubtypesEnum.DYNAMIC:
      self.subtypes = _DynamicSubtypes()
    else:
      raise TypeError(f'bad subtypes argument: {subtypes!r}')

    self.constructible = constructible

  @staticmethod
  def subtype(extends: t.Type, name: str = None) -> t.Callable[[T_Type], T_Type]:
    """
    Decorator for subtypes of the #@unionclass-decorated type *extends*. The *extends* class must
    use #unionclass.Subtypes.DYNAMIC. If a *name* is specified, the class will also be decorated
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
      lambda: f'{extends.__name__} is not using unionclass.Subtypes.DYNAMIC')
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

  def get_type_name(self, type: t.Type) -> str:
    pass

  # Annotation

  def __call__(self, cls: T_Type) -> T_Type:
    if not self.constructible:
      cls.__init__ = unionclass.no_construct
    return super().__call__(cls)


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
