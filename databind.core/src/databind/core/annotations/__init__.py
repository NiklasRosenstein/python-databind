
"""
Annotations in the context of the `databind.core` package provide information about a type or field
that changes the de-/serialization behaviour. Annotations can be attached directly to a type in one
of the following ways:

* directly annotate the type using Python decorator syntax
* pass the annotation along with the field description (see #databind.core.field())
* associate the annotation with a type or field in the #databind.core.ObjectMapper
"""

from .base import Annotation, get_annotation, get_type_annotations, AnnotationsProvider, AnnotationsRegistry, DefaultAnnotationsProvider
from .alias import alias
from .datefmt import datefmt
from .enable_unknowns import enable_unknowns, collect_unknowns
from .fieldinfo import fieldinfo
from .precision import precision
from .typeinfo import typeinfo
from databind.core.types.union import union, unionclass

__all__ = [
  'Annotation',
  'get_annotation',
  'get_type_annotations',
  'AnnotationsProvider',
  'AnnotationsRegistry',
  'DefaultAnnotationsProvider',
  'alias',
  'datefmt',
  'enable_unknowns',
  'collect_unknowns',
  'fieldinfo',
  'precision',
  'typeinfo',
  'union',
  'unionclass',
]
