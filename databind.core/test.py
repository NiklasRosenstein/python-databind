import typing as t
from dataclasses import dataclass
from databind.core.annotations import unionclass

@unionclass(subtypes = unionclass.Subtypes.DYNAMIC)
@dataclass
class Person:
  __init__ = unionclass.no_construct
  name: str

@dataclass
@unionclass.subtype(Person)
class Student(Person):
  visits_courses: t.Set[str]

@dataclass
@unionclass.subtype(Person)
class Teacher(Person):
  teaches_courses: t.Set[str]


Person()
print(Student('John Doe', {'Physics', 'Chemistry'}))