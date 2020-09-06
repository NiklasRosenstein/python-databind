
from pytest import raises
from databind.core import datamodel, field, uniontype
from databind.tagline import dumps, from_str, loads, ParseError

comparisons = [
  ('ld', 'a', 'a'),
  ('ld', 'a=b', {'a': 'b'}),
  ('l', 'a=b,', {'a': 'b'}),
  ('l', '{a=b}', {'a': 'b'}),
  ('l', '{a=b},', [{'a': 'b'}]),
  ('ld', '{a=b},{c=d}', [{'a': 'b'}, {'c': 'd'}]),
  ('ld', 'a{}', {'type': 'a', 'a': {}}),
  ('ld', 'a{b=c}', {'type': 'a', 'a': {'b': 'c'}}),
  ('ld', 'a{b=c},x{u=v,w={a,b,c}}', [{'type': 'a', 'a': {'b': 'c'}}, {'type': 'x', 'x': {'u': 'v', 'w': ['a', 'b', 'c']}}]),

  # TODO: The loader does not currently support escpaed characters.
  #('ld', 'a=foo\\{bar\\}', {'a': 'foo{bar}'}),
]


def test_loader():
  for t, s, v in comparisons:
    if 'l' in t:
      assert loads(s) == v

  with raises(ParseError) as excinfo:
    loads('{a}')
  assert str(excinfo.value) == 'at line 1, col 2: unexpected token Token.BRACE_CLOSE, expected Token.EQUALS or Token.COMMA'

  with raises(ParseError) as excinfo:
    loads('a=b,c')
  assert str(excinfo.value) == 'at line 1, col 5: unexpected token eof, expected Token.EQUALS'

  with raises(ParseError) as excinfo:
    loads('a{b,c}')
  assert str(excinfo.value) == 'at line 1, col 3: unexpected token Token.COMMA, expected Token.EQUALS'


def test_dumper():
  for t, s, v in comparisons:
    if 'd' in t:
      assert s.rstrip(',') == dumps(v)

  with raises(TypeError) as excinfo:
    dumps({'a': object()})
  assert str(excinfo.value) == 'cannot dump value of type object'


def test_conversion():

  @datamodel
  class BindMount:
    src: str
    dst: str
    read_only: bool = field(altname='readonly', default=False)

  @uniontype({
    'bind': BindMount
  }, flat=False)
  class Mount:
    pass

  assert from_str(Mount, 'bind{src=data/,dst=/opt/data}') == BindMount('data/', '/opt/data')
  assert from_str(Mount, 'type=bind,bind={src=data/,dst=/opt/data}') == BindMount('data/', '/opt/data')
  assert from_str(BindMount, 'src=data/,dst=/opt/data,readonly=true') == BindMount('data/', '/opt/data', True)
