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

Databind also makes it easy to define configurable plugin systems:

```python
import abc
from databind.core import datamodel, interface, implementation
from databind.json import from_json, to_json

@interface
class Authenticator(metaclass=abc.ABCMeta):

  @abc.abstractmethod
  def start_oauth2_session(self) -> 'OAuth2Session':
    ...

@datamodel
@implementation('github')
class GithubAuthenticator(Authenticator):
  client_id: str
  client_secret: str

  # ...

github = GithubAuthenticator('id', 'secret')
payload = {'type': 'github', 'client_id': 'id', 'client_secret': 'secret'}

assert to_json(github, Authenticator) == payload
assert from_json(Authenticator, payload) == github
```

---

<p align="center">Copyright &copy; 2020 &ndash; Niklas Rosenstein</p>
