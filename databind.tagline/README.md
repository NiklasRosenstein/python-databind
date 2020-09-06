# databind.tagline

Databind is a library inspired by Jackson-databind to describe and bind data models for
object-oriented programming. The `databind.tagline` module provides functionality to (de-)
serialize strings of comma-separated key-value pairs.

## Syntax

* An object is defined of a comma-separated sequence of key-value pairs
* An array is defined as a sequence of values
* Key-value pairs or values can be grouped/nested with surrounding braces
* Unions can be instantiated by prefixing a brace with the union member name

| Notation | Syntax      | JSON representation    |
| -------- | ----------- | ---------------------- |
| Object   | `a=b,c=d`   | `{"a": "b", "c": "d"}` |
| Array    | `a,b,c`     | `["a", "b", "c"]` |
| Union    | `a{b=c}`    | `{"type": "a", "a": {"b": "c"}}` |
| Nesting  | `a={b=c}`   | `{"a": {"b": "c"}}` |
| Nesting  | `a,{b=c},d` | `["a", {"b": "c"}, "d"]` |

## Quickstart

```python
from databind.core import datamodel, field, uniontype
from databind.tagline import from_str

@datamodel
class BindMount:
  src: str
  dst: str
  read_only: bool = field(altname='readonly', default=False)

@uniontype({
  'bind': BindMount
} flat=False)
class Mount:
  pass

assert from_str(Mount, 'bind{src=data/,dst=/opt/data}') == BindMount('data/', '/opt/data')
assert from_str(Mount, 'type=bind,bind={src=data/,dst=/opt/data}') == BindMount('data/', '/opt/data')
assert from_str(BindMount, 'src=data/,dst=/opt/data,readonly=true') == BindMount('data/', '/opt/data')
```

## Notes

* All values are loaded as strings. It is up to the user of the `load()` function to interpret
  the values as needed. The `dump()` function converts numbers to string for convenience.
* The union syntax is loaded into nested form, which requires that `@uniontype()` are configured
  with `flat=False`.
* The actual data binding is out-sourced with the `databind.json` module (using a custom registry
  initialized with non-strict JSON converters, see `databind.tagline:registry`).
* The loader/dumper does not currently support escaping control characters. Dumping a string
  that contains a control character (like `{` or `,`) will result in output that cannot be
  parsed.

---

<p align="center">Copyright &copy; 2020 Niklas Rosenstein</p>
