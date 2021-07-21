
from io import StringIO
from databind.core import datamodel
from . import from_str, from_stream, to_str, to_stream


@datamodel
class Person:
  name: str
  age: int


def test_to_str():
  assert to_str(Person('John Wick', 55)) == 'age: 55\nname: John Wick\n'
  assert to_str(Person('John Wick', 55), options=dict(sort_keys=False)) == 'name: John Wick\nage: 55\n'


def test_to_stream():
  fp = StringIO()
  to_stream(fp, Person('John Wick', 55))
  assert fp.getvalue() == 'age: 55\nname: John Wick\n'


def test_from_str():
  assert from_str(Person, 'age: 55\nname: John Wick') == Person('John Wick', 55)


def test_from_stream():
  assert from_str(Person, StringIO('age: 55\nname: John Wick')) == Person('John Wick', 55)
