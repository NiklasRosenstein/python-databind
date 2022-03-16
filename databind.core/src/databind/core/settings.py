
from __future__ import annotations
import abc
import decimal
import dataclasses
import enum
import typing as t

import typeapi
from nr.util.generic import T
from nr.util.preconditions import check_instance_of, check_not_none, check_subclass_of

if t.TYPE_CHECKING:
  from databind.core.context import Context
  from databind.core.union import EntrypointUnionMembers, ImportUnionMembers, StaticUnionMembers, UnionMembers

T_Setting = t.TypeVar('T_Setting', bound='Setting')
T_ClassDecoratorSetting = t.TypeVar('T_ClassDecoratorSetting', bound='ClassDecoratorSetting')


class SettingsProvider(abc.ABC):
  """ Interface for providing settings. """

  def get_setting(self, context: Context, setting_type: t.Type[T_Setting]) -> t.Optional[T_Setting]: ...


class Settings(SettingsProvider):
  """ This class is used as a container for other objects that serve as a provider of settings that may taken into
  account during data conversion. Objects that provide settings are instances of #Setting subclasses, such as
  #FieldAlias or #DateFormat.

  Depending on the type of setting, they may be taken into account if present on a field of a dataclass, or globally
  from an instance of the #Settings class that is passed to the #ObjectMapper, or both. Which settings are recognized
  and considered depends also on the implementation of the converter(s) being used.

  The #Settings class provides capabilities to supply global settings, as well as supplying settings conditionally
  based on the type that is being looked at by the #ObjectMapper at the given point in time.

  Example:

  ```py
  from databind.core.settings import DateFormat, Priority, Settings, Strict
  settings = Settings()
  settings.add_global(DateFormat('.ISO_8601', priority=Priority.HIGH))
  settings.add_local(int, Strict(false))
  ```
  """

  def __init__(self, parent: t.Optional[SettingsProvider] = None, global_settings: t.Optional[t.List[Setting]] = None) -> None:
    self.parent = parent
    self.global_settings: t.List[Setting] = list(global_settings) if global_settings else []
    self.local_settings: t.Dict[t.Type, t.List[Setting]] = {}
    self.providers: t.List[t.Callable[[Context], t.List[Setting]]] = []

  def add_global(self, setting: Setting) -> None:
    """ Add a global setting. """

    self.global_settings.append(setting)

  def add_local(self, type_: t.Type, setting: Setting) -> None:
    """ Add a setting locally for a particular Python type. If that Python type is encountered, the settings are
    combined with any other settings that are found for the type. """

    self.local_settings.setdefault(type_, []).append(setting)

  def add_conditional(self, predicate: t.Callable[[Context], bool], setting: Setting) -> None:
    """ Adds a setting conditional on the given *predicate*. """

    def _provider(context: Context) -> None:
      if predicate(context):
        return [setting]
      return []

    self.providers.append(_provider)

  def add_provider(self, provider: t.Callable[[Context], t.List[Setting]]) -> None:
    """ Add a provider callback that is invoked for every conversion context to provide additional settings that
    the subsequent converter should have access to. """

    self.providers.append(provider)

  # SettingsProvider

  def get_setting(self, context: Context, setting_type: t.Type[T_Setting]) -> t.Optional[T_Setting]:

    from nr.util.stream import Stream

    def _all_settings():
      if self.parent:
        setting = self.parent.get_setting(context, setting_type)
        if setting is not None:
          return setting
      if isinstance(context.datatype, typeapi.Type):
        yield from get_class_settings(context.datatype.type, setting_type)
        yield from self.local_settings.get(context.datatype.type, [])
      for provider in self.providers:
        yield from provider(context)
      yield from self.global_settings

    return get_highest_setting(Stream(_all_settings()).of_type(setting_type))


class Priority(enum.IntEnum):
  """ The priority for settings determines their order in the presence of multiple conflicting settings. Settings
  should default to using the #NORMAL priority. The other priorities are used to either prevent overriding a field
  setting globally or to enforce overriding of local field settings globally using #Settings. """

  LOW = 0
  NORMAL = 1
  HIGH = 2
  ULTIMATE = 3


@dataclasses.dataclass
class Setting:
  """ Base class for types of which instances represent a setting to be taken into account during data conversion.
  Every setting has a priority that is used to construct and order or to determine the single setting to use in
  the presence of multiple instances of the same setting type being present.

  Settings are usually attached to dataclass fields using #typing.Annotated, or added to a #Settings object for
  applying the setting globally, but some subclasses may support being used as decorators to attach the setting
  to a type object. Such settings would registers themselves under the `__databind_settings__` attribute (created
  if it does not exist) such that it can be picked up when introspected by a converter. Such #Setting subclasses
  should inherit from #DecoratorSetting instead. """

  priority: Priority

  def __post_init__(self) -> None:
    if type(self) is Setting:
      raise TypeError('Setting cannot be directly instantiated')


class ClassDecoratorSetting(Setting):

  bound_to: t.Optional[t.Type[Setting]] = None

  def __post_init__(self) -> None:
    if type(self) is ClassDecoratorSetting:
      raise TypeError('ClassDecoratorSetting cannot be directly instantiated')
    super().__post_init__()

  def __call__(self, type_: t.Type[T]) -> t.Type[T]:
    """ Decorate the class *type_* with this setting, adding the setting to its `__databind_settings__` list
    (which is created if it does not exist) and sets #bound_to. The same setting instance cannot decorate multiple
    types. """

    assert isinstance(type_, type), type_
    if self.bound_to is not None:
      raise RuntimeError(f'cannot decorate multiple types with the same setting instance')

    self.bound_to = type_
    settings = getattr(type_, '__databind_settings__', None)
    if settings is None:
      settings = []
      setattr(type_, '__databind_settings__', settings)
    settings.append(self)

    return type_


def get_highest_setting(settings: t.Iterable[T_Setting]) -> T_Setting | None:
  """ Return the first, highest setting of *settings*. """

  try:
    return max(settings, key=lambda s: s.priority)
  except ValueError:
    return None


def get_class_settings(type_: t.Type, setting_type: t.Type[T_ClassDecoratorSetting]) -> t.Iterable[T_ClassDecoratorSetting]:
  """ Returns all matching settings on *type_*. """

  for item in getattr(type, '__databind_settings__', []):
    if isinstance(item, setting_type):
      yield item


def get_class_setting(type_: t.Type, setting_type: t.Type[T_ClassDecoratorSetting]) -> T_ClassDecoratorSetting | None:
  """ Returns the first instance of the given *setting_type* on *type_*. """

  return get_highest_setting(get_class_settings(type_, setting_type))


@dataclasses.dataclass
class BooleanSetting(Setting):
  """ Base class for boolean settings. """

  enabled: bool

  def __init__(self, enabled: bool = True, priority = Priority.NORMAL) -> None:
    self.priority = priority
    self.enabled = enabled

  def __post_init__(self) -> None:
    if type(self) is BooleanSetting:
      raise TypeError('BooleanSetting cannot be directly instantiated')
    super().__post_init__()


class Alias(Setting):
  """ The #Alias setting is used to attach one or more alternative names to a dataclass field that should be used
  instead of the field's name in the code.

  Example:

  ```py
  import typing
  from dataclasses import dataclass
  from databind.core.settings import Alias

  @dataclass
  class MyClass:
    my_field: typing.Annotated[int, Alias('foobar', 'spam')]
  ```

  When deserializing a payload, converters should now use `foobar` if it exists, or fall back to `spam` when looking
  up the value for the field in the payload as opposed to `my_field`. When serializing, converters should use `foobar`
  as the name in the generated payload (always the first alias).
  """

  #: A tuple of the aliases provided to the constructor.
  aliases: t.Tuple[str, ...]

  def __init__(self, alias: str, *additional_aliases: str, priority: Priority = Priority.NORMAL) -> None:
    super().__init__(priority)
    self.aliases = (alias,) + additional_aliases

  def __repr__(self) -> str:
    return f'Alias({", ".join(map(repr, self.aliases))}, priority={self.priority!r})'


class Required(BooleanSetting):
  """ Indicates whether a field is required during deserialization, even if it's type specifies that it is an
  optional field.

  Example:

  ```py
  import typing
  from dataclasses import dataclass
  from databind.core.settings import Required

  @dataclass
  class MyClass:
    my_field: typing.Annotated[typing.Optional[int], Required()]
  ```
  """


class Flatten(BooleanSetting):
  """ Indicates whether a field should be "flattened" by virtually expanding it's sub fields into the parent
  datastructure's serialized form.

  Example:

  ```py
  import typing
  from dataclasses import dataclass
  from databind.core.settings import Flatten

  @dataclass
  class Inner:
    a: int
    b: str

  @dataclass
  class Outter:
    inner: typing.Annotated[Inner, Flatten()]
    c: str
  ```

  The `Outter` class in the example above may be deserialized, for example, from a JSON payload of the form
  `{"a": 0, "b": "", "c": ""}` as opposed to `{"inner": {"a": 0, "b": ""}, "c": ""}` due to the `Outter.inner`
  field's sub fields being expanded into `Outter`.
  """


class Strict(BooleanSetting):
  """ Enable strict conversion of the field during conversion (this should be the default for converters unless
  some maybe available option to affect the strictness in a converter is changed). This setting should particularly
  affect only loss-less type conversions (such as `int` to `string` and the reverse being allowed when strict
  handling is disabled). """


@dataclasses.dataclass
class Precision(Setting):
  """ A setting to describe the precision for #decimal.Decimal fields. """

  prec: t.Optional[int] = None
  rounding: t.Optional[str] = None
  Emin: t.Optional[int] = None
  Emax: t.Optional[int] = None
  capitals: t.Optional[bool] = None
  clamp: t.Optional[bool] = None

  def to_decimal_context(self) -> decimal.Context:
    return decimal.Context(
      prec=self.prec, rounding=self.rounding, Emin=self.Emin, Emax=self.Emax,
      capitals=self.capitals, clamp=self.clamp)


@dataclasses.dataclass
class Union(ClassDecoratorSetting):
  """ A setting that decorates a class or can be attached to the #typing.Annotated metadata of a #typing.Union
  type hint to specify that the type should be regarded as a union of more than one types. Which concrete type
  is to be used at the point of deserialization is usually clarified through a discriminator key. Unions may be
  of various styles that dictate how the discriminator key and the remaining fields are to be stored or read
  from.

  For serialiazation, the type of the Python value should inform the converter about which member of the union
  is being used. If the a union definition has multiple type IDs mapping to the same Python type, the behaviour
  is entirely up to the converter (an adequate resolution may be to pick the first matching type ID and ignore
  the remaining matches).

  !!! note

      The the examples for the different styles below, `"type"` is a stand-in for the value of the #discriminator_key
      and `...` serves as a stand-in for the remaining fields of the type that is represented by the discriminator.
  """

  #: The nested style in JSON equivalent is best described as `{"type": "<typeid>", "<typeid>": { ... }}`.
  NESTED: t.ClassVar = 'nested'

  #: The flat style in JSON equivalent is best described as `{"type": "<typeid>", ... }`.
  FLAT: t.ClassVar = 'flat'

  #: The keyed style in JSON equivalent is best described as `{"<typeid>": { ... }}`.
  KEYED: t.ClassVar = 'keyed'

  #: The "best match" style attempts to deserialize the payload in an implementation-defined order and return
  #: the first or best succeeding result. No discriminator key is used.
  BEST_MATCH: t.ClassVar = 'best_match'

  #: The subtypes of the union as an implementation of the #UnionMembers interface. When constructing the #Union
  #: setting, a dictionary may be passed in place of a #UnionMembers implementation, or a list of #UnionMembers
  #: to chain them together.
  members: UnionMembers

  #: The style of the union. This should be one of #NESTED, #FLAT, #KEYED or #BEST_MATCH. The default is #NESTED.
  style: str = NESTED

  #: The discriminator key to use, if valid for the #style. Defaults to `"type"`.
  discriminator_key: str = 'type'

  #: The key to use when looking up the fields for the member type. Only used with the #NESTED style. If not set,
  #: the union member's type ID is used as the key.
  nesting_key: t.Optional[str] = None

  def __init__(
    self,
    members: t.Union[
      UnionMembers,
      StaticUnionMembers._MembersDictType,
      t.List[UnionMembers | StaticUnionMembers._MembersDictType],
      None] = None,
    style: str = NESTED,
    discriminator_key: str = 'type',
    nesting_key: t.Optional[str] = None,
  ) -> None:

    if isinstance(members, dict) or members is None:
      from databind.core.union import StaticUnionMembers
      members = StaticUnionMembers(members or {})
    elif isinstance(members, list):
      from databind.core.union import ChainUnionMembers, StaticUnionMembers
      chain = ChainUnionMembers()
      for item in members:
        if isinstance(item, dict):
          item = StaticUnionMembers(item)
        chain.delegates.append(item)
      members = chain

    self.members = members
    self.style = style
    self.discriminator_key = discriminator_key
    self.nesting_key = nesting_key

  @staticmethod
  def register(extends: t.Type, name: str = None) -> t.Callable[[t.Type[T]], t.Type[T]]:
    """ A convenience method to use as a decorator for classes that should be registered as members of a #Union
    setting that is attached to the type *extends*. The #Union setting on *extends* must have a #StaticUnionMembers
    #members object. The decorated class must also be a subclass of *extends*.

    Example:

    ```py
    import abc
    import dataclasses
    from databind.core.settings import Union

    @Union()
    class MyInterface(abc.ABC):
      # ...
      pass

    @dataclasses.dataclass
    @Union.register(MyInterface, 'some')
    class SomeImplementation(MyInterface):
      # ...
      pass
    ```
    """

    from databind.core.union import StaticUnionMembers

    check_instance_of(extends, type)
    inst = check_not_none(
      get_class_setting(extends, Union),
      lambda: f'{extends.__name__} is not annotated with @union')

    members = check_instance_of(inst.members, StaticUnionMembers)

    def _decorator(subtype: t.Type[T]) -> t.Type[T]:
      check_instance_of(subtype, type)
      check_subclass_of(subtype, extends)
      return members.register(name)(subtype)

    return _decorator

  @staticmethod
  def entrypoint(group: str) -> EntrypointUnionMembers:
    from databind.core.union import EntrypointUnionMembers
    return EntrypointUnionMembers(group)

  @staticmethod
  def import_() -> ImportUnionMembers:
    from databind.core.union import ImportUnionMembers
    return ImportUnionMembers()