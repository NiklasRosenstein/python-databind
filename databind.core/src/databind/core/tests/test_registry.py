
from databind.core import Registry


def test_options_inheritance():
  reg1 = Registry(None)
  reg2 = Registry(reg1)

  reg1.update_options(int, {'strict': True})
  assert dict(reg1.get_options(int)) == {'strict': True}
  assert reg1.get_option(int, 'strict') == True

  assert not reg2._type_options
  assert dict(reg2.get_options(int)) == {'strict': True}
  assert reg2.get_option(int, 'strict') == True

  reg2.update_options(int, {'strict': False})
  assert reg2._type_options
  assert dict(reg2.get_options(int)) == {'strict': False}
  assert reg2.get_option(int, 'strict') == False

  # Ensure reg1 is unchanged.
  assert dict(reg1.get_options(int)) == {'strict': True}
  assert reg1.get_option(int, 'strict') == True
