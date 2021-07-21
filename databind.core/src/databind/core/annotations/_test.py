
from . import Annotation, get_annotation
from dataclasses import dataclass


def test_get_annotation():

  @dataclass
  class MyAnnotation(Annotation):
    message: str

  @MyAnnotation('Hello, World!')
  class MyDataclass:
    pass

  class MySubclass(MyDataclass):
    pass

  assert get_annotation(MyDataclass, MyAnnotation, None) == MyAnnotation('Hello, World!')
  assert get_annotation(MySubclass, MyAnnotation, None) == None
