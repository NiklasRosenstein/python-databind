# Handling unknown keys during deserialization

If you would like to permit extra keys to to be present in a payload that is being deserialized without raising a
`databind.core.converter.ConversionError`, you can use the `databind.core.settings.ExtraKeys` setting
to annotate a `@dataclass`, an annotation or specify it globally to allow extra keys anywhere.

When using this setting, you can also record any unexpected keys so you can report them after the deserialization.

## Allowing extra keys on a dataclass

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

## Allowing extra keys on a dataclass member

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

## Allowing extra keys everywhere

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

## Recording extra keys

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
