# databind.mypy

MyPy plugin for static type validation when using the `databind.core` package.

__Todo__

* [ ] Assignments using `field()` on `@datamodel`s is not yet recognized as valid by Mypy
* [ ] PR Mypy to make `mypy.plugins.dataclasses` customizable for this use case

## Getting started

Install the `databind.mypy` package from PyPI and register it as a MyPy plugin.

```ini
# mypy.ini
[mypy]
plugins = databind.mypy
```

---

<p align="center">Copyright &copy; 2020 Niklas Rosenstein</p>
