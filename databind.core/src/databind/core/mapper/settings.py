
import enum
import typing as t

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

  def __init__(self, *values: _SettingsValue, parent: 'Settings' = None) -> None:
    self._parent = parent
    self._enums: t.Dict[t.Type[enum.Enum], t.Set[enum.Enum]] = {}
    self._objects: t.Dict[t.Type, t.Any] = {}
    for val in values:
      self.set(val)

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
    assert isinstance(of, (type, enum.Enum)), of
    if isinstance(of, enum.Enum):
      return of if of in self._enums.get(type(of), set()) else None
    result = self._objects.get(of)
    if result is None and self._parent is not None:
      result = self._parent.get(of)
    return result

  def unset(self, of: t.Union[_T_Enum, t.Type[_T]]) -> None:
    assert isinstance(of, (type, enum.Enum)), of
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
