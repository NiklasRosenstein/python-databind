
import enum
import typing as t
import nr.preconditions as preconditions

_T = t.TypeVar('_T')
_T_Enum = t.TypeVar('_T_Enum', bound=enum.Enum)
_SettingsValue = t.Union[_T_Enum, _T]


class Settings:
  """
  Container for settings. A setting is either an #enum.Enum instance, or an arbitrary object.

  In the case of an enumeration, multiple values of the same enumeration type may be present in the
  settings at the same time (treated like flags).

  For arbitrary objects, only one instance of a concrete class can be present in the settings at
  any given point in time. Updating the settings with a different object of a type that already has
  an instance of it registered in the settings will override that slot.
  """

  def __init__(self) -> None:
    self._enums: t.Dict[t.Type[enum.Enum], t.Set[enum.Enum]] = {}
    self._objects: t.Dict[t.Type, t.Any] = {}

  def __iter__(self) -> t.Iterable[_SettingsValue]:
    for _enum_type, values in self._enums.items():
      yield from values
    for _type, value in self._objects.items():
      yield value

  @t.overload
  def get(self, of: _T_Enum) -> t.Optional[_T_Enum]: ...

  @t.overload
  def get(self, of: t.Type[_T]) -> t.Optional[_T]: ...

  def get(self, of):
    preconditions.check_instance_of(of, (type, enum.Enum))
    if isinstance(of, enum.Enum):
      return of if of in self._enums.get(type(of), set()) else None
    return self._objects.get(of)

  def unset(self, of: t.Union[_T_Enum, t.Type[_T]]) -> None:
    preconditions.check_instance_of(of, (type, enum.Enum))
    if isinstance(of, enum.Enum):
      self._enums.get(type(of), set()).discard(of)
    else:
      assert isinstance(of, type)
      self._objects.pop(of, None)

  def set(self, value: _SettingsValue) -> None:
    if isinstance(value, enum.Enum):
      self._enums.setdefault(type(value), set()).add(value)
    else:
      if isinstance(value, type):
        raise TypeError(f'cannot set type object as setting')
      self._objects[type(value)] = value

