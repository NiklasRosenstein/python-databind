
import typing as t
import typing_extensions as te
from databind.core.annotations import unionclass
from databind.core.objectmapper import ObjectMapper
from databind.core.schema import Schema
from databind.json import JsonModule

mapper = ObjectMapper.default(JsonModule())


def test_unionclass_from_annotated():
  MyUnion = te.Annotated[t.Union[int, str], unionclass({
    'int': int,
    'str': str
  }, name='MyUnion')]
  assert mapper.deserialize({'type': 'int', 'int': 42}, MyUnion) == 42
  assert mapper.deserialize({'type': 'str', 'str': 'foobar'}, MyUnion) == 'foobar'
  assert mapper.serialize(42, MyUnion) == {'type': 'int', 'int': 42}
  assert mapper.serialize('foobar', MyUnion) == {'type': 'str', 'str': 'foobar'}
