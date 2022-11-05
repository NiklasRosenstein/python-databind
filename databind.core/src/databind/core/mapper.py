from __future__ import annotations

import typing as t

import typeapi
from nr.util.generic import T, U

if t.TYPE_CHECKING:
    from databind.core.context import Direction, Location
    from databind.core.settings import Setting, Settings, SettingsProvider


class ObjectMapper(t.Generic[T, U]):
    """The object mapper is responsible for dispatching the conversion process into a #Module.

    The type parameter *T* represents the deserialized type, while *U* represents the serialized type.
    """

    def __init__(self, settings: t.Optional[Settings] = None) -> None:
        from databind.core.converter import Module
        from databind.core.settings import Settings

        assert isinstance(settings, (type(None), Settings)), settings
        self.module = Module("ObjectMapper.module")
        self.settings = settings or Settings()

    def copy(self) -> ObjectMapper[T, U]:
        new = type(self)(self.settings.copy())
        new.module.converters.extend(self.module.converters)
        return new

    def convert(
        self,
        direction: Direction,
        value: t.Any,
        datatype: t.Union[typeapi.Hint, t.Any],
        location: t.Optional[Location] = None,
        settings: t.Union[SettingsProvider, t.List[Setting], None] = None,
    ) -> t.Any:
        """Convert a value according to the given datatype.

        Arguments:
          direction: (Added in databind.core 0.3.0) The direction (i.e. either deserialization or serialization).
          value: The value to convert.
          datatype: The datatype. If not already a #typeapi.Hint instance, it will be converted using #typeapi.of().
          location: The location of where *value* is coming from. Useful to specify to make debugging easier.
          settings: A list of settings, in which case they will be treated as global settings in addition to the
            mapper's #settings, or an entirely different #SettingsProvider instance (for which it is recommended that
            it is taking the ObjectMapper's #settings into account, for example by passing them for the
            #Settings.parent).

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
            direction=direction,
            value=value,
            datatype=datatype,
            settings=settings or self.settings,
            key=Context.ROOT,
            location=location or Location.EMPTY,
            convert_func=self.module.convert,
        )

        return context.convert()

    def serialize(
        self,
        value: T,
        datatype: t.Union[typeapi.Hint, t.Any],
        filename: t.Optional[str] = None,
        settings: t.Union[SettingsProvider, t.List[Setting], None] = None,
    ) -> U:
        """Serialize *value* according to the its *datatype*."""

        from databind.core.context import Direction, Location

        return t.cast(U, self.convert(Direction.SERIALIZE, value, datatype, Location(filename, None, None), settings))

    def deserialize(
        self,
        value: U,
        datatype: t.Union[typeapi.Hint, t.Any],
        filename: t.Optional[str] = None,
        settings: t.Union[SettingsProvider, t.List[Setting], None] = None,
    ) -> T:
        """Deserialize *value* according to the its *datatype*."""

        from databind.core.context import Direction, Location

        return t.cast(
            T,
            self.convert(Direction.DESERIALIZE, value, datatype, Location(filename, None, None), settings),
        )
