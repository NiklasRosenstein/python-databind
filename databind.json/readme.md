# databind.json

The `databind.json` package implements the de-/serialization to or from JSON payloads using
the `databind.core` framework.

## Quickstart

```py
import databind.json
import dataclasses

@dataclasses.dataclass
class ServerConfig:
  host: str
  port: int = 8080

@dataclasses.dataclass
class MainConfig:
  server: ServerConfig

payload = { 'server': { 'host': '127.0.0.1' } }
config = databind.json.load(payload, MainConfig)
assert config == MainConfig(ServerConfig('127.0.0.1'))
```

## Examples for common use cases

### Unions with literal matches

```py
import dataclasses
import databind.json
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

payload = {"provider": "azure", "resource_group": "foo", "name": "bar"}
assert databind.json.load(payload) == AzureMachine("foo", "bar")
```

---

<p align="center">Copyright &copy; 2020 &ndash; Niklas Rosenstein</p>
