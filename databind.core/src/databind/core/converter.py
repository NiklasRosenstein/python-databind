
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
  """ For any errors that occur during conversion. """

  def __init__(self, message: str, context: Context) -> None:
    self.message = message
    self.context = context

  def __str__(self) -> str:
    import textwrap
    try:
      from databind.core.context import format_context_trace
      return f'{self.message}\nConversion trace:\n{textwrap.indent(format_context_trace(self.context), "  ")}'
    except:
      import traceback
      return traceback.format_exc()


class NoMatchingConverter(ConversionError):
  """ If no converter matched to convert the value and datatype in the context. """

  def __str__(self) -> str:
    return f'no applicable converter found for {self.context.datatype}'
