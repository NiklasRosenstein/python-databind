# databind.json

The `databind.json` package implements the de-/serialization to or from JSON payloads using
the `databind.core` framework.

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
