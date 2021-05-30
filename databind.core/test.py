import typing as t
from dataclasses import dataclass
from databind.core import unionclass

@dataclass
@unionclass(subtypes = unionclass.Subtypes.DYNAMIC, constructible=False)
class Person:
  name: str

@dataclass
@unionclass.subtype(Person)
class Student(Person):
  visits_courses: t.Set[str]

@dataclass
@unionclass.subtype(Person)
class Teacher(Person):
  teaches_courses: t.Set[str]


print(Student('John Doe', {'Physics', 'Chemistry'}))
