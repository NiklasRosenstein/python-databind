
"""
Provides the #fieldinfo() annotation to add additional metadata to a field.
"""

import typing as t
from dataclasses import dataclass
from databind.core.annotations.base import Annotation


@dataclass
class fieldinfo(Annotation):
  #: Mark the field as required even if it's type hint specifies it as #t.Optional
  required: bool = False

  #: Mark the field as "flat", indicating that the fields in this field are expanded into
  #: the parent structure in the serialized form.
  flat: bool = False

  #: Enables strict handling of the field during de/serialization (on by default).
  #:
  #: The behaviour of strict vs. non-strict handling is dependant on the implementation of the
  #: de/serializer. For example, disabling strict de/serialization may enables certain loss-less
  #: type conversion such as string to integer, or the reverse.
  #:
  #: Note that lossy type conversion during de/serialization is usually not recommended for
  #: de/serializer implementations (such as floats with decimal places to integer).
  strict: bool = True
