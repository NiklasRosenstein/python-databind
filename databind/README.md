<h1 align="center">databind</h1>

<p align="center">
  <img src="https://img.shields.io/pypi/pyversions/databind?style=flat" alt="Python versions">
  <a href="https://pypi.org/project/databind/"><img src="https://img.shields.io/pypi/v/databind?flat"></a>
</p>
<p align="center">
  <a href="https://niklasrosenstein.github.io/python-databind/core/basic-usage/">CORE Guide</a> |
  <a href="https://niklasrosenstein.github.io/python-databind/json/examples/">JSON Examples</a>
</p>

## Overview 📖

The `databind` package provides a (de)serialization framework that understands most native Python types as well as
dataclasses, as well as an implementation for serialize to/from JSON-like nested data structures.

Databind is intended mostly for flexible and easy to use configuration loading. It's goal is not to provide high-performance payload serde, you should look towards [mashumaro](https://pypi.org/project/mashumaro/) for this usecase.

### Example

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

## Notable release notes

### 4.5.0

* Merged `databind.core` and `databind.json` packages into `databind`. The old PyPI packages will remain as proxies
  until the next minor version.
* Dropped support for Python 3.6 and 3.7.

---

<p align="center">Copyright &copy; 2022 &ndash; Niklas Rosenstein</p>
