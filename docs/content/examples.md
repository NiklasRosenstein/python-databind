# Examples

This page shows some common usage examples for using the `databind.json` library.

## Configuration deserialization

A common use case is to describe the configuration for an application as dataclasses, then deserialize it from a
JSON, YAMl or TOML file.

```py
from __future__ import annotations
import databind.json
import dataclasses
import tomlib
from pathlib import Path

@dataclasses.dataclass
class ServerConfig:
    host: str
    port: int = 8080

@dataclasses.dataclass
class MainConfig:
    server: ServerConfig

    @staticmethod
    def load(path: Path | str) -> MainConfig:
        data = tomlib.loads(Path(path).read_text())
        return databind.json.load(data, MainConfig, filename=path)

config = MainConfig.load_toml("config.toml")
```

An example config TOML file that can be parsed with the above configuration:

```toml
[server]
host = "localhost"
port = 8080
```

Note that any extra keys that are not expected per the schema will raise a `databind.core.converter.ConversionError`.

!!! danger Runtime type introspection

    Databind uses Python runtime type annotation introspection using the [`typeapi`][typeapi] package. This requires
    that all type annotations that databind comes in contact with must be valid expressions in the current Python
    version, even if `from __future__ import annotations` is used.

    This means if your code needs to be compatible with Python versions lower than 3.10 or 3.9 that you can not
    use the new type union syntax (`a | b`) or built-in generic aliases (such as `list[int]`) and need to continue
    to use `typing.Union`, `typing.Optional` and `typing.List`, etc.

[typeapi]: https://pypi.org/project/typeapi/

## Permitting unknown keys

If you would like to permit extra keys to to be present in a payload that is being deserialized without raising a
`databind.core.converter.ConversionError`, you can use the `databind.core.settings.ExtraKeys` setting
to annotate a `@dataclass`, an annotation or specify it globally to allow extra keys anywhere.

When using this setting, you can also record any unexpected keys so you can report them after the deserialization.

### Allowing extra keys on a dataclass

```py
# cat <<EOF | python -
from dataclasses import dataclass
from databind.core.settings import ExtraKeys
from databind.json import load

@ExtraKeys()
@dataclass
class MyClass:
    a: int

assert load({"a": 42, "b": "ignored"}, MyClass) == MyClass(42)
```

!!! note Non-transitive setting

    The `ExtraKeys` setting does not apply transitively to the members of the dataclass.

### Allowing extra keys on a dataclass member

```py
# cat <<EOF | python -
from dataclasses import dataclass
from databind.core.settings import ExtraKeys
from databind.json import load
from typing_extensions import Annotated

@dataclass
class Sub:
    a: int

@dataclass
class Main:
    sub: Annotated[Sub, ExtraKeys()]

assert load({"sub": {"a": 42, "b": "ignored"}}, Main) == Main(Sub(42))

# However this:

load({"sub": {"a": 42}, "b": "not ignored!"}, Main)

# Gives:
# databind.core.converter.ConversionError: encountered extra keys: {'b'}
#  Conversion trace:
#     $: Type(__main__.Main)
```

### Allowing extra keys everywhere

Providing the `ExtraKeys()` setting to the `settings` of a deserialization process will enable it for all schemas,
except for those that have a different setting "closer by" (you can use `ExtraKeys(False)` to explicitly _not_ permit extra keys).

```py
# cat <<EOF | python -
from dataclasses import dataclass
from databind.core.settings import ExtraKeys
from databind.json import load

@dataclass
class MyClass:
    a: int

assert load({"a": 42, "b": "ignore"}, MyClass, settings=[ExtraKeys()]) == MyClass(42)
```

### Recording extra keys

You can also record which extra keys have been encountered to report. This is common if you want to allow but
warn about unused keys in a payload.

```py
# cat <<EOF | python -
from dataclasses import dataclass
from databind.core.settings import ExtraKeys
from databind.core.context import format_context_trace
from databind.json import load

@dataclass
class MyClass:
    a: int

recorded = []
assert load({"a": 42, "b": "ignore"}, MyClass, settings=[ExtraKeys(recorder=lambda ctx, keys: recorded.append((ctx, keys)))]) == MyClass(42)

for ctx, keys in recorded:
    print("warning: unused keys", keys, "at")
    print(format_context_trace(ctx))

# Gives:
#
# warning: unused keys {'b'} at
#   $: Type(__main__.MyClass)
```

## Dynamic unions with union mappers

Todo

## Unions with literal discriminators

When unions are deserialized, they can be accommodated by a "union mapper" to identify based on a value in the
payload how that payload can be deserialized.

However, you can also use `Literal` type hints on dataca,sses in combination with naive union types. The `Literal`
will fail to deserialize if the value in the payload does not match with the literal value, and naive union types will
try all types in the union in order and return the first successfully deserialized type.

!!! note

    Arguably this is rather inefficient; a better implementation would be to prioritize checking values of literal
    fields first so we don't need to attempt to deserialize the rest if there's no match.

```py
# cat <<EOF | python -
import dataclasses
from databind.json import load
from typing import Literal

@dataclasses.dataclass
class AwsMachine:
  region: str
  name: str
  instance_id: str
  provider: Literal["aws"] = "aws"

@dataclasses.dataclass
class AzureMachine:
  resource_group: str
  name: str
  provider: Literal["azure"] = "azure"

Machine = AwsMachine | AzureMachine

payload = {
    "provider": "azure",
    "resource_group": "foo",
    "name": "bar",
}
assert load(payload, Machine) == AzureMachine("foo", "bar")
```
