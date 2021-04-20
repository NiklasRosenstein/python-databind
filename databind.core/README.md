# databind.core

A `jackson-databind` inspired de-/serialization library for Python based on `@dataclass`es.

## Introduction

The `databind.core` package does not provide a concrete de-/serializer, but additions and
extensions on top of the built-in `dataclasses` module to describe serialization behaviour. The
`@dataclass` decorator and `field()` method provided by this package can act as a drop-in
replacement, while providing some additional features such as

* non-optional fields following optional fields
* common class and field annotations
* union types

To de-/serialize data, choose one of the following libraries:

* [databind.binary](https://pypi.org/projects/databind.binary)
* [databind.json](https://pypi.org/projects/databind.json)
* [databind.tagline](https://pypi.org/projects/databind.tagline)
* [databind.yaml](https://pypi.org/projects/databind.yaml)

> __Note__: Any of these de/-serializer implementations can work with the classes decorated by the
> standard-library `@dataclasses.dataclass` decorator. Use `databind.core.dataclass` and
> `databind.core.field` if you need to customize the de-/serialization behaviour.

Use the [databind.mypy](https://pypi.org/projects/databind.yaml) for Mypy type-checking
support when using the `databind.core` methods.

## Example

```py
from databind.core import dataclass, unionclass

@unionclass(subtypes = unionclass.Subtypes.DYNAMIC)
class Person:
  name: str

@dataclass
@unionclass.subtype(Person)
class Student(Person):
  visits_courses: set[str]

@dataclass
@unionclass.subtype(Person)
class Teacher(Person):
  teaches_courses: set[str]
```

Example using `databind.json` to deserialize a JSON payload from this datamodel:

```py
from databind.json import from_json
student = from_json({
  'type': 'student',
  'student': {
    'name': 'John Doe',
    'visitsCourses': [
      'Physics',
      'Chemistry'
    ]
  }
})
assert isinstance(student, Student)
assert student.name == 'John Doe'
assert student.visits_courses == {'Physics', 'Chemistry'}
```

---

<p align="center">Copyright &copy; 2020 &ndash; Niklas Rosenstein</p>
