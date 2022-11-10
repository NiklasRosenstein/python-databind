# databind

__Compatibility__: Python 3.6.3+

Databind is a library inspired by jackson-databind to de-/serialise Python dataclasses.

If you install the `databind` package, you will get the respective version of the
following packages:

* [databind.core](https://pypi.org/project/databind.core/) &ndash; Provides the core framework.
* [databind.json](https://pypi.org/project/databind.json/) &ndash; De-/serialize dataclasses to/from JSON payloads.

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
