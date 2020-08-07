# databind.core

Databind is a library inspired by Jackson-databind to describe and bind data models for
object-oriented programming. The `databind.core` package provides the abstractions to
generalize the (de-) serialization process such that it can be implemented for arbitrary
data formats.

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

Then you'll need to pick a serialization library. Below is an example for `databind.yaml`:

```python
from databind import yaml

person = yaml.from_str(Person, '''
name: John Wick
age: 55
''')

assert isinstance(person, Person)
assert person.name == 'John Wick'

print(yaml.to_str(person))
```

---

<p align="center">Copyright &copy; 2020 &ndash; Niklas Rosenstein</p>
