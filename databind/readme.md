# databind

Databind is a library inspired by jackson-databind to de-/serialise Python dataclasses. The `databind` package
will install the full suite of databind packages. Compatible with Python 3.7 and newer.

* [databind.core](https://pypi.org/project/databind.core/) &ndash; Provides the core framework.
* [databind.json](https://pypi.org/project/databind.json/) &ndash; De-/serialise dataclasses to/from JSON payloads.

## Supported features

| Feature | Python version | Databind version |
| ------- | -------------- | ---------------- |
| [PEP585](https://www.python.org/dev/peps/pep-0585/) | 3.9 | 1.2.0 &ndash; *current* |
| [PEP585](https://www.python.org/dev/peps/pep-0585/) (forward references) | 3.9 | 1.3.1? &ndash; *current* |
| Resolve type parameters of specialised generic types | 3.x | 1.5.0 &ndash; *current* |
| `typing.TypedDict` | 3.x | 2.0.0 &ndash; *current* |
| Concretise type variables in parametrised generics | 3.x | 2.0.0 &ndash; *current* |

---

<p align="center">Copyright &copy; 2022 &ndash; Niklas Rosenstein</p>
