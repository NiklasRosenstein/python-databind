
from __future__ import annotations
import abc
import logging
import typing as t

import typeapi

if t.TYPE_CHECKING:
  from databind.core.context import Context

logger = logging.getLogger(__name__)


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

  def __init__(self, context: Context, message: str) -> None:
    self.context = context
    self.message = message

  def __str__(self) -> str:
    import textwrap
    from databind.core.context import format_context_trace

    try:
      return f'{self.message}\nConversion trace:\n{textwrap.indent(format_context_trace(self.context), "  ")}'
    except:
      logger.exception('Exception while formatting context traceback')
      raise

  @staticmethod
  def expected(ctx: Context, types: t.Union[t.Type, t.Sequence[t.Type]], got: t.Optional[t.Type] = None) -> ConversionError:
    if isinstance(types, type):
      types = (types,)
    expected = '|'.join(typeapi.type_repr(t) for t in types)
    got = type(ctx.value) if got is None else got
    return ConversionError(ctx, f'expected {expected}, got {typeapi.type_repr(got)} instead')


class NoMatchingConverter(ConversionError):
  """ If no converter matched to convert the value and datatype in the context. """

  def __init__(self, context: Context) -> None:
    super().__init__(context, f'no applicable converter found for {context.datatype}')
