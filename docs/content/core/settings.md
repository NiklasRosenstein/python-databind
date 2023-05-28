# Settings

Settings in Databind are Python objects that convey additional information to the serialization process. A setting
must be expicitly supported by a {@pylink databind.core.converter.Converter} in order to take effect. As such, all
settings provided by `databind.core` merely provide a standard set of settings that should but may not all be supported
by serialization lirbary implementations.

Settings must be subclasses from {@pylink databind.core.settings.Setting}, {@pylink databind.core.settings.BooleanSetting}
or {@pylink databind.core.settings.ClassDecoratedSetting}.

## Specifying settings

You can specify settings at various places in your code to make them apply at various stages during the serialization.
The following list shows the order of precedence, from highest to lowest:

1. Type-hint local settings specified in the metadata of `typing.Annotated` hints.
2. Settings that were used to annotate a type.
3. Global settings that are passed to {@pylink databind.core.mapper.ObjectMapper.convert}, or the respective
  `serialize`/`deserialize` methods.

## Settings priority

The above precedence only takes effect within the same priority group. The priority of all setting defaults to `NORMAL`
unless specified otherwise. The following priority groups exist:

* `LOW`: Settings with this priority group are resolved after `NORMAL` settings.
* `NORMAL`: The default priority group.
* `HIGH`: Settings with this priority group are resolved before `NORMAL` settings.
* `ULTIMATE`: Settings with this priority group are resolved before `HIGH` settings.

Converters are usually only interested in the first instance of any setting type.
