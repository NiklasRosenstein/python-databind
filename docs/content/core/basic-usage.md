# Basic Usage

## Implementing a custom converter

Implementing your own serialization functions is easy. It's often needed, not only when implementing a new
serialization format next to the `databind.json` module, but also to extend an existing serialization format. For
example, you may want to add support for serializing your `URI` custom type to and from a string. You can do this
by implementing a custom {@pylink databind.core.converter.Converter}.

```python
from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Any

from databind.core.context import Context
from databind.core.converter import Converter


@dataclass
class URI:
    scheme: str
    host: str
    path: str

    def __str__(self) -> str:
        return f'{self.scheme}://{self.host}{self.path}'

    class URIConverter(Converter):

        def convert(self, ctx: Context) -> Any:
            if not isinstance(ctx.datatype, ClassTypeHint) or not issubclass(ctx.datatype.type, URI):
                raise NotImplementedError
            if ctx.direction.is_serialize():
                return str(ctx.value)  # Always serialize into string
            elif ctx.direction.is_deserialize():
                if isinstance(ctx.value, str):
                    parsed = urlparse(ctx.value)
                    return URI(parsed.scheme, parsed.hostname, parsed.path)
                # Fall back to other converters, such as default implementation for dataclasses
                raise NotImplementedError
            assert False, 'invalid direction'
```

To use this new converter, you need to register it to an {@pylink databind.core.mapper.ObjectMapper} instance.

```python
from databind.core.mapper import ObjectMapper

mapper = ObjectMapper()
mapper.module.register(URI.URIConverter())

assert mapper.deserialize('https://example.com/foo', URI) == URI('https', 'example.com', '/foo')
assert mapper.serialize(URI('https', 'example.com', '/foo'), URI) == 'https://example.com/foo'
```

## Supporting settings in your converter

!!! info "What are settings?"

    "Settings" are Python objects that are associated with types in the serialization process that can alter the behavior
    of the converter. Go to [Settings](settings.md) to read more about it.

Consuming settings in a converter is straight forward. The {@pylink databind.core.context.Context} class provides
convenient methods to access settings that are relevant for the current value being processed.

```python
#  ...
from databind.core.settings import BooleanSetting


@dataclass
class URI:
    # ...

    class SerializeAsString(BooleanSetting):
        """
        Specifies whether the URI should be serialized to a string.
        """

    class URIConverter(Converter):

        def convert(self, ctx: Context) -> Any:
            if not isinstance(ctx.datatype, ClassTypeHint) or not issubclass(ctx.datatype.type, URI):
                raise NotImplementedError
            if ctx.direction.is_serialize():
                serialize_as_string = ctx.get_setting(URI.SerializeAsString).enabled
                if serialize_as_string:
                    return str(ctx.value)
                raise NotImplementedError
            elif ctx.direction.is_deserialize():
                if isinstance(ctx.value, str):
                    parsed = urlparse(ctx.value)
                    return URI(parsed.scheme, parsed.hostname, parsed.path)
                raise NotImplementedError
            assert False, 'invalid direction'
```

The setting can now be specified when serializing a `URI` instance as a global setting:

```python
# ...

from databind.core.converter import NoMatchingConverter
from pytest import raises

# When the setting is not enabled, the converter raises a NotImplementedError, having databind search for
# another applicable converter. Since none exists with an otherwise empty ObjectMapper, this raises a
# NoMatchingConverter exception.
with raises(NoMatchingConverter):
    mapper.serialize(URI('https', 'example.com', '/foo'), URI)

# Using a global setting, affecting all URI instances being serialized unless a more local setting is specified.
assert mapper.serialize(
    URI('htps', 'example.com', '/foo'), URI, settings=[URI.SerializeAsString(True)]) == 'https://example.com/foo'
```

## Supporting `typing.Annotated` type hints

Converters must explicitly support `typing.Annotated` type hints. They are often useful to associate settings with
a type in a particular case only. There may also be other reasons that a user may want to use an `Annotated` type
hint.

```python
class URI:
    # ...

    class URIConverter(Converter):

        def convert(self, ctx: Context) -> Any:
            # Check if the type to be converted is supposed to be a URI.
            datatype = ctx.datatype
            if isinstance(datatype, AnnotatedTypeHint):
                datatype = datatype[0]
            if not isinstance(datatype, ClassTypeHint) or not issubclass(datatype.type, URI):
                raise NotImplementedError

            # ...
```

Now the setting can be specified as an `Annotated` type hint:

```python
# Using the Annotated type hint to associate the setting with the type.
assert mapper.serialize(
    URI('https', 'example.com', '/foo'), Annoated[URI, URI.SerializeAsString(True)]) == 'https://example.com/foo'
```

## Class-decorator settings

There is also a special class called {@pylink databind.core.settings.ClassDecoratorSetting}, which can be used to
create setting types that can decorate classes. The `Context.get_settings()` method will automatically understand
that setting as well.

## Simplifying custom converts for users

Implementing custom converters, especially to convert between strings and custom types, can be a bit tedious. Given
that it is quite a common use case, it is usually recommended that a Databind serialization library provide specific
settings to simplify the process for users.

For example, the `databind.json` package provides a {@pylink databind.json.settings.JsonConverter} setting that users
can use to very easily support the serialization of their custom types to and from strings in a JSON context.

```python
from databind.json.settings import JsonConverter

@JsonConverter.using_classmethods(serialize="__str__", deserialize="of")
class MyCustomType:

    def __str__(self) -> str:
        ...

    @staticmethod
    def of(s: str) -> MyCustomType:
        ...
```
