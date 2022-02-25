# databind.core

`databind.core` provides a jackson-databind inspired framework for data de-/serialization in Python. Unless you
are looking to implement support for de-/serializing new data formats, the `databind.core` package alone might
not be what you are looking for (unless you want to use `databind.core.dataclasses` as a drop-in replacement to
the standard library `dataclasses` module, for that check out the section at the bottom).

### Known implementations

* [databind.json](https://pypi.org/project/databind.json)

### Dataclass extension

The standard library `dataclasses` module does not allow to define non-default arguments after default arguments.
You can use `databind.core.dataclasses` as a drop-in replacement to get this feature. It behaves exactly like the
standard library, only that non-default arguments may follow default arguments. Such arguments can be passed to
the constructor as positional or keyword arguments.

```py
from databind.core import dataclasses

@dataclasses.dataclass
class A:
  value1: int = 42

@dataclasses.dataclass
class B(A):
  value2: str

print(B(0, 'Hello, World!'))
print(B(value2='Answer to the universe'))
```

---

<p align="center">Copyright &copy; 2020 &ndash; Niklas Rosenstein</p>
