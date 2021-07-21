from databind.binary import to_bytes, calc_size, cstr, u32
from databind.core import datamodel, field

@datamodel
class RiffChunk:
  """ RIFF-WAVE chunk header. """
  chunk_id: cstr = field(default=b'RIFF', metadata={'size': 4})
  chunk_size: u32
  riff_type: cstr = field(default=b'WAVE', metadata={'size': 4})

assert calc_size(RiffChunk) == 12
assert to_bytes(RiffChunk(chunk_size=16442)) == b'RIFF:@\x00\x00WAVE'