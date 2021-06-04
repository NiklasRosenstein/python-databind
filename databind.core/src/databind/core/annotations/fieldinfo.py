
"""
Provides the #fieldinfo() annotation to add additional metadata to a field.
"""

import typing as t
from dataclasses import dataclass
from . import Annotation


@dataclass
class fieldinfo(Annotation):
  #: Mark the field as required even if it's type hint specifies it as #t.Optional
  required: bool = False

  #: Mark the field as "flat", indicating that the fields in this field are expanded into
  #: the parent structure in the serialized form.
  flat: bool = False
