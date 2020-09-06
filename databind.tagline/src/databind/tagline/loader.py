
import enum
import string
from typing import Any, Optional

from nr.parsing import core as _parsing


class ParseError(Exception):

  def __init__(self, filename: Optional[str], cursor: _parsing.Cursor, msg: str) -> None:
    self.filename = filename
    self.cursor = cursor
    self.msg = msg

  def __str__(self):
    message = 'at line {}, col {}'.format(self.cursor.lineno, self.cursor.colno)
    if self.filename:
      message = 'in "' + self.filename + '" ' + message
    return message + ': ' + self.msg


class Token(enum.Enum):
  WHITESPACE = enum.auto()
  VALUE = enum.auto()
  COMMA = enum.auto()
  EQUALS = enum.auto()
  BRACE_OPEN = enum.auto()
  BRACE_CLOSE = enum.auto()


class ValueType(enum.Enum):
  ANY = enum.auto()
  LIST = enum.auto()
  OBJECT = enum.auto()


class Loader:

  RULES = [
    _parsing.Regex(Token.WHITESPACE, string.whitespace, skip=True),
    _parsing.Regex(Token.VALUE, r'[^\{\},=]+'),
    _parsing.Keyword(Token.COMMA, ','),
    _parsing.Keyword(Token.EQUALS, '='),
    _parsing.Keyword(Token.BRACE_OPEN, '{'),
    _parsing.Keyword(Token.BRACE_CLOSE, '}'),
  ]

  def __init__(self, text: str, filename: Optional[str] = None) -> None:
    self.filename = filename
    self.scanner = _parsing.Scanner(text)
    self.lexer = _parsing.Lexer(self.scanner, self.RULES)

  def parse(self):
    result = self._parse_expression(ValueType.ANY)
    if self.lexer.token.type != _parsing.eof:
      raise self._unexpected_token(_parsing.eof)
    return result

  def _parse_expression(self, context: ValueType, expect: ValueType = ValueType.ANY, from_nested: bool = False):
    object_result = {}
    list_items = []
    comma_consumed = False
    value_type = expect

    for token in self.lexer:
      if value_type in (ValueType.ANY, ValueType.LIST) and token.type == Token.BRACE_OPEN:
        value_type = ValueType.LIST
        list_items.append(self._parse_nested())
      elif token.type == Token.VALUE:
        value = self._parse_single_value(value_type)
        if (value_type == ValueType.ANY and isinstance(value, tuple)) or value_type == ValueType.OBJECT:
          if not isinstance(value, tuple):
            raise self._unexpected_token(Token.EQUALS)
          object_result[value[0]] = value[1]
          value_type = ValueType.OBJECT
        else:
          list_items.append(value)
          value_type = ValueType.LIST
      elif token.type == Token.COMMA and context in (ValueType.ANY, ValueType.LIST):
        comma_consumed = True
      else:
        break

    if value_type == ValueType.OBJECT:
      assert not list_items
      return object_result
    elif value_type == ValueType.LIST:
      assert not object_result
      if comma_consumed:
        return list_items

      if from_nested:
        raise self._unexpected_token(f'{Token.EQUALS} or {Token.COMMA}')
      return list_items[0]

    assert False, "uhh"

  def _parse_single_value(self, context: ValueType):
    if self.lexer.token.type == Token.VALUE:
      # This could be three things: 1) a key-value pair, 2) a union notation, 3) just a value
      value = self.lexer.token.value.group().strip()
      token = self.lexer.next()
      if context in (ValueType.ANY, ValueType.OBJECT) and token.type == Token.EQUALS:  # 1) a key-value pair
        self.lexer.next()
        return (value, self._parse_expression(ValueType.OBJECT))
      elif token.type == Token.BRACE_OPEN:  # 2) a union notation
        members = self._parse_nested(expect=ValueType.OBJECT)
        assert isinstance(members, dict), "expected union members"
        return {'type': value, value: members}
      else:  # 3) just a value
        return value
    elif self.lexer.token.type == Token.BRACE_OPEN:
      # Just a nested notation.
      return self._parse_nested()

  def _parse_nested(self, expect: ValueType = ValueType.ANY):
    assert self.lexer.token.type == Token.BRACE_OPEN, "expected BRACE_OPEN ({)"
    self.lexer.next()
    result = self._parse_expression(ValueType.ANY, expect=expect, from_nested=True)
    if self.lexer.token.type != Token.BRACE_CLOSE:
      raise self._unexpected_token(Token.BRACE_CLOSE)
    self.lexer.next()
    return result

  def _unexpected_token(self, expected: str) -> ParseError:
    token = self.lexer.token
    raise ParseError(self.filename, token.cursor,
      f'unexpected token {token.type}, expected {expected}')


def loads(string: str, filename: Optional[str] = None) -> ValueType:
  return Loader(string, filename).parse()
