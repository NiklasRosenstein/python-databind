
import abc
import dataclasses
import enum
import pkg_resources
import typing as t
import weakref

from .types import AnnotatedType, BaseType, ConcreteType, ObjectType, from_typing


@dataclasses.dataclass
class UnionTypeError(Exception):
  type: t.Union[str, t.Type, BaseType]
  subtypes: 'IUnionSubtypes'

  def __str__(self) -> str:
    owner = self.subtypes.owner() if self.subtypes.owner else None
    typ = self.type.__name__ if isinstance(self.type, type) else str(self.type)
    return f'type `{typ}` is not a member of @unionclass `{owner.__name__ if owner else "<unknown>"}`'


class IUnionSubtypes(abc.ABC):
  """
  This interface describes the subtypes of a union type.
  """

  owner: t.Optional['weakref.ref[t.Type]']

  @abc.abstractmethod
  def get_type_name(self, type: BaseType) -> str:
    """
    Given a type that is a member of the union subtypes, return the name of the type
    that is used as a discriminator when serializing a value of the type. Raises a
    #UnionTypeError exception if *type* is not a member of this union subtypes.
    """

  @abc.abstractmethod
  def get_type_by_name(self, name: str) -> BaseType:
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


class EntrypointSubtypes(IUnionSubtypes):
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

  def get_type_name(self, type_: BaseType) -> str:
    if isinstance(type_, AnnotatedType):
      type_ = type_.type
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

  def get_type_by_name(self, name: str) -> BaseType:
    try:
      return from_typing(self._entrypoints[name].load())
    except KeyError:
      raise UnionTypeError(name, self)

  def get_type_names(self) -> t.List[str]:
    return list(self._entrypoints.keys())


class DynamicSubtypes(IUnionSubtypes):

  def __init__(self) -> None:
    self._members: t.Dict[str, BaseType] = {}

  def __repr__(self) -> str:
    return f'DynamicSubtypes(members={self.get_type_names()})'

  def get_type_name(self, type: BaseType) -> str:
    for key, value in self._members.items():
      if value == type:
        return key
    raise UnionTypeError(type, self)

  def get_type_by_name(self, name: str) -> BaseType:
    try:
      return self._members[name]
    except KeyError:
      raise UnionTypeError(name, self)

  def get_type_names(self) -> t.List[str]:
    return list(self._members.keys())

  def add_type(self, name: str, type_: t.Union[BaseType, t.Type, t.Any]) -> None:
    if not isinstance(type_, BaseType):
      type_ = from_typing(type_)
    if name in self._members:
      raise RuntimeError(f'type {name!r} already registered')
    self._members[name] = type_


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
