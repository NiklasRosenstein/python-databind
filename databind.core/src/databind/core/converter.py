
from __future__ import annotations
import abc
import typing as t

if t.TYPE_CHECKING:
  from databind.core.context import Context


class Converter(abc.ABC):
  """ Interface for converting a value from one representation to another. """

  @abc.abstractmethod
  def convert(self, ctx: Context) -> t.Any:
    """ Convert the value in *ctx* to another value.

    Argument:
      ctx: The conversion context that contains the value, datatype, settings, location and allows you to
        recursively continue the conversion process for sub values.
    Raises:
      NotImplementedError: If the converter does not support the conversion for the given context.
    Returns:
      The new value.
    """


class ConversionError(Exception):

  def __init__(self, message: str, context: Context) -> None:
    self.message = message
    self.context = context

  def __str__(self) -> str:
    from databind.core.context import format_context_trace
    message = f'{self.message}\n  Conversion trace:\n{self.context.get_trace().format()}'
    if self.tried:
      message += '\n  Tried converters:\n' + '\n'.join(f'    - {c}' for c in self.tried)
    return message
