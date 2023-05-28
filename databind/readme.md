# `databind`

Databind is a Python serialization library on top of dataclasses, inspired by similar libraries from other languages
like [jackson-databind](https://github.com/FasterXML/jackson-databind) and [serde-rs](https://serde.rs/).

![Python versions](https://img.shields.io/pypi/pyversions/pydoc-markdown?style=for-the-badge)
[![Pypi version](https://img.shields.io/pypi/v/pydoc-markdown?style=for-the-badge)](https://pypi.org/project/pydoc-markdown/)

[Examples](https://niklasrosenstein.github.io/python-databind/examples/) | [Changelog](https://niklasrosenstein.github.io/python-databind/changelog/databind.core/)

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

* Support for a plethora of builtin types, including `Enum`, `datetime`, `date`, `time`, `timedelta`, `uuid`, `pathlib.Path`
* Support for multiple union serialization modes (nested, flat, keyed, `typing.Literal`)
* Support for generic types, e.g. `load([{"name": "Jane Doe"}], list[Person])`
* Support for new-style type hints in older Python versions when using forward refererences (strings or `__future__.annotations`) thanks to [typeapi][]
    * [PEP 604 - Allow writing union types as X | Y](https://www.python.org/dev/peps/pep-0604/)
    * [PEP585 - Type Hinting Generics in Standard Collections](https://www.python.org/dev/peps/pep-0585/))
* Full runtime type checking during serialization

---

<p align="center">Copyright &copy; 2022 &ndash; Niklas Rosenstein</p>
