
import abc
import typing_extensions as te
import dataclasses
from databind.core.annotations import fieldinfo, union
from databind.json import loads


@dataclasses.dataclass
class Person:
  name: str
  age: te.Annotated[int, fieldinfo(strict=False)]


@union()
class Plugin(abc.ABC):
  pass


@union.subtype(Plugin)
@dataclasses.dataclass
class PluginA(Plugin):
  pass


@union.subtype(Plugin, name = 'plugin-b')
@dataclasses.dataclass
class PluginB(Plugin):
  value: str


def test_loads():
  assert loads('42', int) == 42
  assert loads('{"name": "John", "age": 20}', Person) == Person('John', 20)
  assert loads('{"name": "John", "age": "20"}', Person) == Person('John', 20)  # Allowed because of fieldinfo(strict=False)
  assert loads('{"type": "PluginA", "PluginA": {}}', Plugin) == PluginA()
  assert loads('{"type": "PluginA"}', Plugin, annotations=[union(style=union.Style.flat)]) == PluginA()
  assert loads('{"type": "plugin-b", "plugin-b": {"value": "foobar"}}', Plugin) == PluginB("foobar")
  assert loads('{"type": "plugin-b", "value": "foobar"}', Plugin, annotations=[union(style=union.Style.flat)]) == PluginB("foobar")
