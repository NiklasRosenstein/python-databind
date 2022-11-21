# databind.json

The `databind.json` package implements the de-/serialization to or from JSON payloads using
the `databind.core` framework.

Check out the [Documentation][0] for examples.

[0]: https://niklasrosenstein.github.io/python-databind/

## Built-in converters

The following tables shows which types can be deserialized from / serialize to Python types with the native
converters provided by the `databind.json` module:

| Converter name | Types | Description |
| -------------- | ----- | ----------- |
| `AnyConverter` | `typing.Any` | Accept any value (useful for arbitrary JSON). |
| `CollectionConverter` | `typing.Collection[T]`, excl. `str`, `bytes`, `bytearray`, `memoryview` and `typing.Mapping[K, V]` | Converts between native Python collections and JSON arrays. |
| `DatetimeConverter` | `datetime.date`, `datetime.datetime`, `datetime.time` | Converts between strings and date/time formats, using ISO 8601 time format by default (can be changed with the `databind.core.settings.DateFormat` setting). |
| `DecimalConverter` | `decimal.Decimal` | Converts between strings (and ints/floats if strict mode is off, strict mode is on by default) and decimals. The precision can be controlled with the `databind.core.settings.Precision` setting. |
| `EnumConverter` | `enum.Enum`, `enum.IntEnum` | Convert between strings and Python enumerations. The serialized form of `IntEnum` is the integer value, whereas the serialized form of `Enum` is a string (name of the enumeration value). |
| `MappingConverter` | `typing.Mapping[K, V]` | Converts between Python dicts and JSON objects. (While in theory `K` can be any type, for JSON `K` always needs to be `str`). |
| `OptionalConverter` | `typing.Optional[T]` | Handles optional fields in a schema. |
| `PlainDatatypeConverter` | `bytes`, `str`, `int`, `float`, `bool` | Converts between plain datatypes. In non-strict mode (off by default), numeric types will also accept strings as input for the deserialization. |
| `SchemaConverter` | `dataclasses.dataclass`, `typing.TypedDict` | Converts between Python dataclasses or typed dictionary and JSON objects. |
| `UnionConverter` | `typing.Union[...]` | Handles union types. Unions in JSON can be expressed in a multitide of ways, e.g. using a discriminator key and flat, keyed or nested structure or "best match". Check out the examples section of the documentation for more information. |
| `LiteralConverter` | `typing.Literal[...]` | Accepts or rejects a value based on whether it matches one of the values in the literal type hint. |


The following converters are provided for convenience:

| Converter name | Types | Description |
| -------------- | ----- | ----------- |
| `StringifyConverter` | n/a | A helper that allows to easily create de/serializers from a "to string" and "from string" function. |

The following additional types are natively supported by `databind.json` using `StringifyConverter`:

| Types | Description |
| ----- | ----------- |
| `uuid.UUID` | Convert between strings and UUIDs. |
| `pathlib.Path` | Convert between strings and paths. |
| `pathlib.PurePath` | Convert between strings and paths. |
| `nr.date.duration` | Deserialize from ISO 8601 duration strings or the object form, serialize to ISO 8601 strings. |

---

<p align="center">Copyright &copy; 2020 &ndash; Niklas Rosenstein</p>
