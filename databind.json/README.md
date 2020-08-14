# databind.json

Databind is a library inspired by Jackson-databind to describe and bind data models for
object-oriented programming. The `databind.json` package provides converters for JSON data
types, data models and union types to serialize and deserialize JSON payloads.

## Quickstart

```python
from typing import Optional
from databind.core import datamodel
from databind.json import from_json

@datamodel
class Geolocation:
  latitude: float
  longitude: float
  altitude: Optional[float] = None

@datamodel
class ResolvedLocation:
  query: str
  location: Geolocation

london = from_json(ResolvedLocation, {
  "query": "London",
  "location": {
    "latitude": 51.507351,
    "longitude": -0.127758,
  },
})

assert london == ResolvedLocation("London", Geolocation(51.507351, -0.127758))
```

---

<p align="center">Copyright &copy; 2020 &ndash; Niklas Rosenstein</p>
