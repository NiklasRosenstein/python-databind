# databind.core

Databind is a library inspired by Jackson-databind to describe and bind data models for
object-oriented programming. The `databind.core` package provides the abstractions to
generalize the (de-) serialization process such that it can be implemented for arbitrary
data formats.

Databind requires Python 3.6+ because of it's dependency on class-member type hints and
the `dataclasses` module (for which there exists a backport from Python 3.7 to 3.6 on
PyPI).

## Quickstart

```python
from databind.core import datamodel, field
from typing import Optional

@datamodel
class Person:
  """ Class that represents a person's details. """
  name: str
  age: Optional[int] = field(default=None)
  address: Optional[str] = field(default=None)
```

Then you'll need to pick a serialization library. Below is an example for `databind.json`:

```python
from databind import json

person = json.from_str(Person, '{"name": "John Wick", "age": 55}')

assert isinstance(person, Person)
assert person.name == 'John Wick'

print(json.to_str(person))
```

---

<p align="center">Copyright &copy; 2020 &ndash; Niklas Rosenstein</p>
