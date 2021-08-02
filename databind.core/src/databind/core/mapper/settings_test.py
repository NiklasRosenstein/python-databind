
import enum
from dataclasses import dataclass
from .settings import Settings


def test_settings():

  class MyEnum(enum.Enum):
      A = enum.auto()
      B = enum.auto()

  @dataclass(frozen=True)
  class MyClass:
    name: str

  settings = Settings()
  settings.set(MyEnum.A)
  settings.set(MyClass('foobar'))

  assert settings.get(MyEnum.A) == MyEnum.A
  assert settings.get(MyEnum.B) == None
  assert settings.get(MyClass) == MyClass('foobar')
  assert set(settings) == {MyEnum.A, MyClass('foobar')}

  settings.set(MyEnum.B)
  settings.set(MyClass('spam'))

  assert settings.get(MyEnum.A) == MyEnum.A
  assert settings.get(MyEnum.B) == MyEnum.B
  assert settings.get(MyClass) == MyClass('spam')
  assert set(settings) == {MyEnum.A, MyEnum.B, MyClass('spam')}

  settings.unset(MyEnum.A)
  settings.unset(MyClass)

  assert settings.get(MyEnum.A) == None
  assert settings.get(MyEnum.B) == MyEnum.B
  assert settings.get(MyClass) == None
  assert set(settings) == {MyEnum.B}
