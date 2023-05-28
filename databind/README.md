<h1 align="center">databind</h1>

<p align="center">
  <img src="https://img.shields.io/pypi/pyversions/databind?style=for-the-badge" alt="Python versions">
  <a href="https://pypi.org/project/databind/"><img src="https://img.shields.io/pypi/v/databind?style=for-the-badge"></a>
</p>
<p align="center"><i>
Databind is a Python serialization library on top of dataclasses, inspired by similar libraries from other languages
like <a href="https://github.com/FasterXML/jackson-databind">jackson-databind</a> and <a href="https://serde.rs/">serde-rs</a>.</i>
</p>
<p align="center">
  <a href="https://niklasrosenstein.github.io/python-databind/core/basic-usage/">CORE Guide</a> |
  <a href="https://niklasrosenstein.github.io/python-databind/json/examples/">JSON Examples</a>
</p>

## Overview 📖

The `databind.core` package provides the core framework for databind. It is then used by `databind.json` to provide
comprehensive serializatio support between Python and JSON-like data structure. The serialization can easily be
extended to YAML or TOML by combining it with respective libraries (e.g. `pyaaml` and `tomli`).

```python
@dataclass
class Server:
    host: str
    port: int

@dataclass
class Config:
    server: Server

from databind.json import dump, load
assert load({"server": {"host": "localhost", "port": 8080}}, Config) == Config(server=Server(host='localhost', port=8080))
assert dump(Config(server=Server(host='localhost', port=8080)), Config) == {"server": {"host": "localhost", "port": 8080}}
```

If you install the `databind` proxy package, you get matching versions of `databind.core` and `databind.json`.

## Features ✨

  [typeapi]: https://github.com/NiklasRosenstein/python-typeapi

* Support for a plethora of builtin types, including `Enum`, `Decimal`, `UUID`, `Path`, `datetime`, `date`, `time`, `timedelta`
* Support for multiple union serialization modes (nested, flat, keyed, `typing.Literal`)
* Support for generic types, e.g. `load([{"name": "Jane Doe"}], list[Person])`
* Support for new-style type hints in older Python versions when using forward refererences (strings or `__future__.annotations`) thanks to [typeapi][]
    * [PEP 604 - Allow writing union types as X | Y](https://www.python.org/dev/peps/pep-0604/)
    * [PEP585 - Type Hinting Generics in Standard Collections](https://www.python.org/dev/peps/pep-0585/))
* Support for customized serialization and deserialization of types
* Support for flattening fields of a nested dataclass or collecting remaining fields in a `dict`
* Full runtime type checking during serialization
* Use "settings" to customize serialization behaviour
    * As global settings per `load()`/`dump()` call: `load(..., settings=[ExtraKeys(True)])`
    * As class-level settings using a decorator: `@Union(style=Union.FLAT)` or `@ExtraKeys(True)`
    * As type-hint level settings using `typing.Annotated` (or `typing_extensions.Annotated`): `full_name: Annotated[str, Alias("fullName")]` or `FullNameField = Annotated[str, Alias("fullName")]`

---

<p align="center">Copyright &copy; 2022 &ndash; Niklas Rosenstein</p>
