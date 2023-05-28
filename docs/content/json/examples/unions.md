# Defining Unions

## Dynamic unions with union mappers

Todo

## Using `typing.Literal` as discriminator

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
