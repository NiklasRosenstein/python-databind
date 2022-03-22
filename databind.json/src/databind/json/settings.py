
import typing as t
from databind.core.converter import ConversionError
from databind.core.context import Context
from databind.core.settings import Priority, Setting


class ExtraKeys(Setting):
  """ If discovered while deserializing a #databind.core.schema.Schema, it's callback is used to inform when extras
  keys are encountered. If the setting is not available, or if the arg is set to `False` (the default), it will
  cause an error.

  The setting may also be supplied at an individual schema level. """

  def __init__(self, arg: t.Union[bool, t.Callable[[Context, t.Set[str]], t.Any]], priority: Priority = Priority.NORMAL) -> None:
    self.arg = arg
    self.priority = priority

  def inform(self, ctx: Context, extra_keys: t.Set[str]) -> None:
    if self.arg is False:
      raise ConversionError(ctx, f'encountered extra keys: {extra_keys}')
    elif self.arg is not True:
      self.arg(ctx, extra_keys)
