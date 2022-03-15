
from __future__ import annotations
from xdrlib import ConversionError
import dataclasses
import typing as t

import typeapi

if t.TYPE_CHECKING:
  from databind.core.settings import SettingsProvider, T_Setting


class Location(t.NamedTuple):
  """ Represents a location in a file. """

  #: The name of the file.
  filename: t.Optional[str]

  #: The line number in the file.
  line: t.Optional[int]

  #: The column number in the file.
  column: t.Optional[int]


@dataclasses.dataclass
class Context:
  """ The context is constructed by the #ObjectMapper and passed to an applicable #Converter to convert #value
  according to the #datatype. """

  #: The parent context.
  parent: t.Optional[Context]

  #: The value to convert.
  value: t.Any

  #: The expected datatype of the value to inform the converter of what to convert the #value from or to.
  datatype: typeapi.Hint

  #: A list of #Setting#s that are to be taken into account by the converter which can potentialy impact
  #: the conversion process.
  settings: SettingsProvider

  #: The key or index under which #value is present in the source material relative to the #parent context.
  #: This is `None` only for the root value in the same source.
  key: t.Union[int, str, None]

  #: The location of the #value in the source material.
  location: Location

  #: A function to dispatch the further conversion of a #Context.
  convert_func: t.Callable[[Context], t.Any]

  def get_setting(self, setting_type: t.Type[T_Setting]) -> T_Setting | None:
    """ Retrieve a setting by type that for the current context. """

    return self.settings.get_setting(setting_type)

  def spawn(
    self,
    value: t.Any,
    datatype: t.Union[typeapi.Hint, t.Any],
    key: t.Union[int, str, None],
    location: t.Optional[Location] = None,
  ) -> Context:
    """ Spawn a sub context with a new value, datatype, key and optionally a new location. If the location is
    not overwritten, the parent filename is inherited, but not line number and column.

    Arguments:
      value: The value to convert.
      datatype: The datatype of *value*. If this is not already a #typeapi.Hint, it will be converted to one
        using #typeapi.of().
      key: The key or index at which the *value* can be found relative to the parent.
      location: The location of the new value. If not specified, the parent filename is inherited but not the
        line number and column.
    Returns:
      A new #Context object that has *self* as its #parent.
    """

    if not isinstance(datatype, typeapi.Hint):
      datatype = typeapi.of(datatype)

    if location is None:
      location = Location(self.location.filename, None, None)

    return Context(self, value, datatype, self.settings, key, location)

  def convert(self) -> t.Any:
    """ Invoke the #convert_func with *self*. """

    return self.convert_func(self)

  def error(self, message: str) -> ConversionError:
    return ConversionError(message)

  def iter_hierarchy_up(self) -> t.Iterable[Context]:
    current: t.Optional[Context] = self
    while current:
      yield current
      current = current.parent


def format_context_trace(ctx: Context) -> str:
  """ Formats a trace for the given context that is convenient to inspect in case of errors to understand where the
  context is pointing to in the payload that is being converted. """

  lines = []
  prev_filename: t.Optional[str] = None
  for ctx in reversed(list(ctx.iter_hierarchy_up())):

    # On the first context, or if the filename changed, we output the filename.
    if prev_filename is None or (ctx.location.filename != prev_filename and ctx.location.filename is not None):
      lines.append(f'In "{ctx.location.filename}"')
      prev_filename = ctx.location.filename

    if ctx.key is None:
      key = '$'
    elif isinstance(ctx.key, str):
      key = f'.{ctx.key}'
    elif isinstance(ctx.key, int):
      key = f'[{ctx.key}]'
    else:
      raise TypeError(f'encountered unexpected type in Context.key: {ctx.key.__class__.__name__!r}')

    line = f'  {key}: {ctx.datatype}'
    if ctx.location.line or ctx.location.column:
      line = f'{line} (at {ctx.location.line}:{ctx.location.column})'

    lines.append(line)

  return '\n'.join(line)
