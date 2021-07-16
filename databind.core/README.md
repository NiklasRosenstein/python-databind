# databind.core

`databind.core` provides a framework for data de-/serialization in Python.

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

## See also

* [databind.binary](https://pypi.org/projects/databind.binary)
* [databind.json](https://pypi.org/projects/databind.json)
* [databind.tagline](https://pypi.org/projects/databind.tagline)
* [databind.yaml](https://pypi.org/projects/databind.yaml)

---

<p align="center">Copyright &copy; 2020 &ndash; Niklas Rosenstein</p>
