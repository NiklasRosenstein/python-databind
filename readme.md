# databind

Databind is a library inspired by jackson-databind to de-/serialize Python dataclasses. The `databind` package
will install the full suite of databind packages. Compatible with Python 3.7 and newer.

* [databind.core](https://pypi.org/project/databind.core/) &ndash; Provides the core framework.
* [databind.json](https://pypi.org/project/databind.json/) &ndash; De-/serialize dataclasses to/from JSON payloads.

__Not yet migrated to 1.x__

* [databind.mypy](https://pypi.org/project/databind.mypy/) &ndash; A Mypy plugin for `databind.core`
* [databind.binary](https://pypi.org/project/databind.binary/)
* [databind.tagline](https://pypi.org/project/databind.tagline/)
* [databind.yaml](https://pypi.org/project/databind.yaml/)

## Supported features

| Feature | Python version | Databind version |
| ------- | -------------- | ---------------- |
| [PEP585](https://www.python.org/dev/peps/pep-0585/) | 3.9 | 1.2.0 &ndash; *current* |
| [PEP585](https://www.python.org/dev/peps/pep-0585/) (forward references) | 3.9 | 1.3.1? &ndash; *current* |

---

<p align="center">Copyright &copy; 2020 &ndash; Niklas Rosenstein</p>