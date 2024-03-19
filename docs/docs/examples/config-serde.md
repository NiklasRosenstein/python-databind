# Configuration Serde

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
    use the new type union syntax (`a | b`) or built-in generic aliases (such as `t.List[int]`) and need to continue
    to use `typing.Union`, `typing.Optional` and `typing.List`, etc.

[typeapi]: https://pypi.org/project/typeapi/
