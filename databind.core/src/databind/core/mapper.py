
from __future__ import annotations
import typing as t

import typeapi
from nr.util.generic import T

if t.TYPE_CHECKING:
  from databind.core.context import Location
  from databind.core.settings import Setting, Settings, SettingsProvider


class ObjectMapper:
  """ The object mapper is responsible for constructing a conversion #Context and dispatching it for conversion to
  a matching #Converter implementation. """

  def __init__(self, settings: t.Optional[Settings] = None) -> None:
    from databind.core.converter import Module
    from databind.core.settings import Settings
    assert isinstance(settings, (type(None), Settings)), settings
    self.module = Module('ObjectMapper.module')
    self.settings = settings or Settings()

  def copy(self) -> ObjectMapper:
    new = type(self)(self.settings.copy())
    new.module.converters.extend(self.module.converters)
    return new

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

    context = Context(
      parent=None,
      value=value,
      datatype=datatype,
      settings=settings or self.settings,
      key=Context.ROOT,
      location=location or Location.EMPTY,
      convert_func=self.module.convert,
    )

    return context.convert()


class BiObjectMapper(t.Generic[T]):
  """ A convenience helper that manages two object mappers, one for serialization and another for deserialization.

  Type arguments:
    T: Narrows the return type of #serialize() and *value* parameter of #deserialize().
  """

  def __init__(self, serializer: ObjectMapper, deserializer: ObjectMapper) -> None:
    """
    Arguments:
      serializer: The #ObjectMapper to use in #serialize().
      deserializer: The #ObjectMapper to use in #deserialize().
    """
    self.serializer = serializer
    self.deserializer = deserializer

  def serialize(
    self,
    value: t.Any,
    datatype: t.Union[typeapi.Hint, t.Any],
    filename: t.Optional[str] = None,
    settings: t.Union[SettingsProvider, t.List[Setting], None] = None,
  ) -> T:
    """ Serialize *value* according to the its *datatype*. """

    from databind.core.context import Location
    return self.serializer.convert(value, datatype, Location(filename, None, None), settings)

  def deserialize(
    self,
    value: T,
    datatype: t.Union[typeapi.Hint, t.Any],
    filename: t.Optional[str] = None,
    settings: t.Union[SettingsProvider, t.List[Setting], None] = None,
  ) -> T:
    """ Deserialize *value* according to the its *datatype*. """

    from databind.core.context import Location
    return self.deserializer.convert(value, datatype, Location(filename, None, None), settings)
