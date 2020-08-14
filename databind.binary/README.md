# databind.binary

Databind is a library inspired by Jackson-databind to describe and bind data models for
object-oriented programming. The `databind.binary` package implements conversion of data
models between Python and binary format (using the `struct` module).

__Todo__

* [ ] Support (efficient) unpacking of nested structs

## Quickstart

```python
from databind.binary import to_bytes, calc_size, cstring, u32
from databind.core import datamodel, field

@datamodel
class RiffChunk:
  """ RIFF-WAVE chunk header. """
  chunk_id: cstring(4) = field(default=b'RIFF')
  chunk_size: u32
  riff_type: cstring(4) = field(default=b'WAVE')

assert calc_size(RiffChunk) == 12
assert to_bytes(RiffChunk(chunk_size=16442)) == b'RIFF:@\x00\x00WAVE'
```

---

<p align="center">Copyright &copy; 2020 &ndash; Niklas Rosenstein</p>
