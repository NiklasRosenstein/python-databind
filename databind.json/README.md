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
config = databind.json.load(MainConfig, payload)
assert config == MainConfig(ServerConfig('127.0.0.1'))
```

---

<p align="center">Copyright &copy; 2020 &ndash; Niklas Rosenstein</p>
