# Pitfalls

## Missing type parameters

Databind will not simply assume `Any` for a type hint when it is not set. Instead, it will raise an error like to
following when an unbound type parameter is encountered:

    databind.core.converter.NoMatchingConverter: no deserializer for `TypeHint(~T_Page)` and payload of type `dict`

> Note: The handling of missing type parameter depends on the serde implementation (e.g. `databind.json`), but it is a
> convention that all implementations should follow by default.

__Examples__

(1)

```py
from databind.json import load

load([1, "foo", {"name": "Doe"}], list)  # could not find item type in TypeHint(list)
```

(2)

```py
from dataclasses import dataclass
from databind.json import load
from typing import Generic, TypeVar

T = TypeVar("T", bound="MyClass")

@dataclass
class MyClass(Generic[T]):
    children: list[T]

load({"children": [{"children": []}]}, MyClass)  # no deserializer for `TypeHint(~T)` and payload of type `dict`
```

The example (2) can only be fixed by creating a dedicated subclass:

```py
@dataclass
class MySpecificClass(MyClass["MySpecificClass"]):
    pass

load({"children": [{"children": []}]}, MySpecificClass)
```
