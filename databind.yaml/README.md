# databind.yaml

Databind is a library inspired by Jackson-databind to describe and bind data models for
object-oriented programming. The `databind.yaml` module provides functionality to (de-)
serialize YAML payloads from/to Python objects.

> __Note:__ This module is just a thin wrapper that provides utility functions, combining the
> functionality of [databind.json](https://pypi.org/project/databind.json/) with PyYAML.

## Quickstart

```python
from typing import Optional
from databind.core import datamodel
from databind.yaml import from_str

@datamodel
class Geolocation:
  latitude: float
  longitude: float
  altitude: Optional[float] = None

@datamodel
class ResolvedLocation:
  query: str
  location: Geolocation

london = from_str(ResolvedLocation, '''
query: London
location:
  latitude: 51.507351
  longitude: -0.127758
''')

assert london == ResolvedLocation("London", Geolocation(51.507351, -0.127758))
```

---

<p align="center">Copyright &copy; 2020 Niklas Rosenstein</p>
