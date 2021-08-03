
import logging
import traceback
import typing as t
from databind.core import Context, ConversionError, Converter, ImplicitUnionType

logger = logging.getLogger(__name__)


def _get_log_level(logger: t.Optional[logging.Logger]) -> int:
  while logger and logger.level == 0:
    logger = logger.parent
  if logger:
    return logger.level
  return 0


def _indent_exc(exc: str) -> str:
  lines = []
  for index, line in enumerate(str(exc).splitlines()):
    if index > 0:
      line = '| ' + line
    lines.append(line)
  return '\n'.join(lines)


class ImplicitUnionConverter(Converter):

  def convert(self, ctx: Context) -> t.Any:
    assert isinstance(ctx.type, ImplicitUnionType)

    errors: t.List[str] = []
    tracebacks: t.List[str] = []
    is_debug = _get_log_level(logger) >= logging.DEBUG

    for type_ in ctx.type.types:
      try:
        return ctx.push(type_, ctx.value, None, ctx.field).convert()
      except ConversionError as exc:
        errors.append(f'{type_}: {exc}')
        if is_debug:
          tracebacks.append(traceback.format_exc())
    if is_debug:
      logger.debug(
        f'Error converting `{ctx.type}` ({ctx.direction.name}). This message is logged in '
        f'conjunction with a ConversionTypeError to provide information about the tracebacks '
        f'that have been caught when converting the individiual union members. This might not '
        f'indicate an error in the program if the exception is handled.\n'
        + '\n'.join(tracebacks))
    errors_text = '\n'.join(errors)
    raise ctx.error(_indent_exc(
      f'expected {ctx.type}, got `{type(ctx.value).__name__}`\n{errors_text}'))
