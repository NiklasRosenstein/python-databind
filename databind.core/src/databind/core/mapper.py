
from __future__ import annotations
import typing as t

import typeapi

if t.TYPE_CHECKING:
  from databind.core.context import Context, Location
  from databind.core.module import Module
  from databind.core.settings import Settings


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

  def convert(self, context: Context) -> t.Any:
    for module in self.modules:
      for converter in module.converters:
        try:
          return converter.convert(context)
        except NotImplementedError:
          pass
    raise NoMatchingConverter(context.datatype)

  def convert_value(
    self,
    value: t.Any,
    datatype: t.Union[typeapi.Hint, t.Any],
    location: t.Optional[Location] = None,
  ) -> t.Any:
    from databind.core.context import Context, Location
    if not isinstance(datatype, typeapi.Hint):
      datatype = typeapi.of(datatype)
    context = Context(None, value, datatype, self.settings, None, location or Location.EMPTY, self.convert)
    return context.convert()


class NoMatchingConverter(Exception):

  def __init__(self, datatype: typeapi.Hint) -> None:
    self.datatype = datatype

  def __str__(self) -> str:
    return f'no applicable converter found for {self.datatype}'
