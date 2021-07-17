
import databind.core.annotations as A
from databind.core.objectmapper import Module
from databind.core.types import AnnotatedType, BaseType, ConcreteType, ObjectType, UnionType


class UnionclassAdapter(Module):
  """
  Adapter for classes decorated with #@A.unionclass().
  """

  def adapt_type_hint(self, type_: BaseType) -> BaseType:
    if isinstance(type_, ConcreteType):
      unionclass = A.get_annotation(type_.type, A.unionclass, None)
    elif isinstance(type_, AnnotatedType):
      unionclass = A.get_annotation(type_.annotations, A.unionclass, None)
    elif isinstance(type_, ObjectType) and type_.schema.unionclass:
      unionclass = type_.schema.unionclass
    else:
      unionclass = None
    if unionclass:
      return UnionType(
        unionclass.subtypes,
        unionclass.get_style(),
        unionclass.get_discriminator_key(),
        type_.to_typing())
    return type_
