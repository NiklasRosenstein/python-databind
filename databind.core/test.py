import typing as t
from dataclasses import dataclass, field
from databind.core.annotations.alias import alias
from databind.core.annotations.datefmt import datefmt
from databind.core.annotations.unionclass import unionclass
from databind.core.api import Context
from databind.core.location import Location
from databind.core.objectmapper import ObjectMapper
from databind.core.typehint import Concrete
from databind.json import JsonModule

@dataclass
@unionclass(subtypes = unionclass.Subtypes.DYNAMIC, constructible=False)
class Person:
  name: str

@dataclass
@unionclass.subtype(Person)
class Student(Person):
  visits_courses: t.Set[str]

  class _annotations:
    visits_courses = [alias('teaches-courses')]

mapper = ObjectMapper(JsonModule())

import datetime

val = mapper.deserialize('2021-05-01', datetime.datetime, annotations=[datefmt('%Y-%m-%d')])
print(val, repr(val))

val = mapper.serialize(val, datetime.datetime, annotations=[datefmt('%d-%m-%Y')])
print(val, repr(val))

#v = Student('John Doe', {'Physics', 'Chemistry'})
#print(mapper.deserialize(v, Student))

