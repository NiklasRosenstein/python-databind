
import typing as t
import typing_extensions as te
from dataclasses import dataclass

import nr.preconditions as preconditions

from databind.core.union import ChainSubtypes, DynamicSubtypes, EntrypointSubtypes, IUnionSubtypes, ImportSubtypes, UnionStyle
from . import Annotation, get_annotation
from .typeinfo import typeinfo

T_Type = t.TypeVar('T_Type', bound=t.Type)


class _Subtypes:
  dynamic: te.Final = DynamicSubtypes
  entrypoint: te.Final = EntrypointSubtypes
  chain: te.Final = ChainSubtypes
  import_: te.Final = ImportSubtypes


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

  Examples:

  ```py
  import abc
  import dataclasses
  from databind.core import unionclass

  @unionclass()
  @dataclasses.dataclass
  class Person:
    name: str

  @unionclass.subtype(Person)
  @dataclasses.dataclass
  class Student(Person):
      courses: t.Set[str]

  @unionclass(subtypes = unionclass.Subtypes.entrypoint('my.entrypoint'))
  class IPlugin(abc.ABC):
    pass # ...
  ```
  """

  Subtypes = _Subtypes
  Style = UnionStyle

  subtypes: IUnionSubtypes
  style: t.Optional[UnionStyle]
  discriminator_key: t.Optional[str]
  constructible: bool
  name: t.Optional[str]
  decorated_type: t.Optional[t.Type]

  def __init__(self,
    subtypes: t.Union[IUnionSubtypes, t.Sequence[t.Type], t.Mapping[str, t.Type]] = None,
    *,
    style: t.Optional[UnionStyle] = None,
    discriminator_key: t.Optional[str] = None,
    constructible: bool = False,
    name: str = None,
  ) -> None:

    self.subtypes = DynamicSubtypes()
    if isinstance(subtypes, IUnionSubtypes):
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
    self.constructible = constructible
    self.name = name
    self.decorated_type = None

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
    subtypes = preconditions.check_instance_of(inst.subtypes, DynamicSubtypes,
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

  # Annotation

  def __call__(self, cls: T_Type) -> T_Type:
    if not self.constructible:
      cls.__init__ = unionclass.no_construct
    self.decorated_type = None
    return super().__call__(cls)
