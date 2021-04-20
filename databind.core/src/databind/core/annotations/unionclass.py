
import abc
import enum
import typing as t
import nr.preconditions as preconditions
from . import Annotation, get_annotation
from .typeinfo import typeinfo


T_Type = t.TypeVar('T_Type', bound=t.Type)


class _ISubtypes(metaclass=abc.ABCMeta):
  # @:change-id unionclass.ISubtypes
  pass


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


class unionclass(Annotation):
  # @:change-id !databind.core.unionclass
  """
  Used to annotate that a class describes a union.

  Note that if the decorated class provides properties that should be inherited by the child
  dataclasses, you need to also decorate the class as a `@dataclass`. You may choose to set
  the `__init__` method to #unionclass.no_construct to prevent the creation of instances of the
  #@unionclass` decorated class.

  Example:

  ```py
  from databind.core import unionclass

  @unionclass(subtypes = unionclass.Subtypes.DYNAMIC)
  @dataclass
  class Person:
    __init__ = unionclass.no_consruct
    name: str

  Person('John Doe')  # TypeError
  ```
  """

  Subtypes = _Subtypes
  ISubtypes = _ISubtypes

  def __init__(self, *, subtypes: U_Subtypes) -> None:
    """
    Create a union class decorator.

    The *subtypes* may be one of the following:

    * #unionclass.Subtypes.DYNAMIC
    * #unionclass.Subtypes.ENTRYPOINT()
    * #unionclass.ISubtypes implementation
    * A list of types
    """

    self.subtypes = subtypes
    self.registered_subtypes: t.List[t.Type] = []

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
    preconditions.check_argument(inst.subtypes == _Subtypes.DYNAMIC,
      lambda: f'{extends.__name__} is not using unionclass.Subtypes.DYNAMIC')
    def decorator(subtype: T_Type) -> T_Type:
      preconditions.check_subclass_of(subtype, extends)
      inst.registered_subtypes.append(subtype)
      if name is not None:
        subtype = typeinfo(name)(subtype)
      return subtype
    return decorator

  @staticmethod
  def no_construct(self: t.Any) -> None:
    """
    This class is not constructible. Use any of it's subtypes.
    """

    raise TypeError(f'@unionclass {type(self).__name__} is not constructible')
