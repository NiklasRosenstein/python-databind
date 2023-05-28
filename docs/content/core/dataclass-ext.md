# Dataclass extension

The standard library `dataclasses` module does not allow to define non-default arguments after default arguments.
You can use `databind.core.dataclasses` as a drop-in replacement to get this feature. It behaves exactly like the
standard library, only that non-default arguments may follow default arguments. Such arguments can be passed to
the constructor as positional or keyword arguments.

!!! note

    You will loose Mypy type checking support for dataclasses decorated with `databind.core.dataclasses.dataclass`.

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
