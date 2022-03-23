
import typing as t

import typeapi
from databind.core.context import Context, format_context_trace, Location
from databind.core.settings import Settings


def test_format_context_trace():
  settings = Settings()
  location = Location.EMPTY
  def no_convert(*a): raise NotImplementedError
  ctx1 = Context(None, {'a': 1}, typeapi.of(t.Dict[str, int]), settings, Context.ROOT, location, no_convert)
  ctx2 = Context(ctx1, 1, typeapi.of(int), settings, 'a', location, no_convert)
  assert format_context_trace(ctx1) == (
    '  $: Type(dict, nparams=2, args=(Type(str), Type(int)))'
  )
  assert format_context_trace(ctx2) == (
    '  $: Type(dict, nparams=2, args=(Type(str), Type(int)))\n'
    '  .a: Type(int)'
  )
