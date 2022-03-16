
from __future__ import annotations
import typing as t

import typeapi

if t.TYPE_CHECKING:
  from databind.core.context import Context, Location
  from databind.core.module import Module
  from databind.core.settings import Setting, Settings, SettingsProvider


class ObjectMapper:
  """ The object mapper is responsible for constructing a conversion #Context and dispatching it for conversion to
  a matching #Converter implementation. """

  def __init__(self, settings: t.Optional[Settings] = None) -> None:
    from databind.core.settings import Settings
    assert isinstance(settings, (type(None), Settings)), settings
    self.settings = settings or Settings()
    self.modules: t.List[Module] = []

  def add_module(self, module: Module) -> None:
    """ Add a module to the mapper. """

    from databind.core.module import Module
    assert isinstance(module, Module), module
    self.modules.append(module)

  def _convert_context(self, ctx: Context) -> t.Any:
    from databind.core.converter import NoMatchingConverter

    for module in self.modules:
      for converter in module.converters:
        try:
          return converter.convert(ctx)
        except NotImplementedError:
          pass

    raise NoMatchingConverter(ctx)

  def convert(
    self,
    value: t.Any,
    datatype: t.Union[typeapi.Hint, t.Any],
    location: t.Optional[Location] = None,
    settings: t.Union[SettingsProvider, t.List[Setting], None] = None,
  ) -> t.Any:
    """ Convert a value according to the given datatype.

    Arguments:
      value: The value to convert.
      datatype: The datatype. If not already a #typeapi.Hint instance, it will be converted using #typeapi.of().
      location: The location of where *value* is coming from. Useful to specify to make debugging easier.
      settings: A list of settings, in which case they will be treated as global settings in addition to the
        mapper's #settings, or an entirely different #SettingsProvider instance (for which it is recommended that
        it is taking the ObjectMapper's #settings into account, for example by passing them for the #Settings.parent).
    Raises:
      ConversionError: For more generic errosr during the conversion process.
      NoMatchingConverter: If at any point during the conversion a datatype was encountered for which no matching
        converter was found.
      """

    from databind.core.context import Context, Location
    from databind.core.settings import Settings

    if not isinstance(datatype, typeapi.Hint):
      datatype = typeapi.of(datatype)
    if isinstance(settings, list):
      settings = Settings(self.settings, global_settings=settings)
    context = Context(None, value, datatype, settings or self.settings, Context.ROOT, location or Location.EMPTY, self._convert_context)
    return context.convert()
