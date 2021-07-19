
import typing as t
import weakref
import databind.core.annotations as A
from databind.core.api import ITypeHintAdapter
from databind.core.objectmapper import Module
from databind.core.types import AnnotatedType, BaseType, ConcreteType, ObjectType, UnionType


class UnionclassAdapter(Module):
  """
  Adapter for classes decorated with #@A.unionclass().
  """

  def adapt_type_hint(self, type_: BaseType, adapter: t.Optional[ITypeHintAdapter] = None) -> BaseType:
    if isinstance(type_, ConcreteType):
      unionclass = A.get_annotation(type_.type, A.unionclass, None)
    elif isinstance(type_, AnnotatedType):
      unionclass = A.get_annotation(type_.annotations, A.unionclass, None)
    elif isinstance(type_, ObjectType) and type_.schema.unionclass:
      unionclass = type_.schema.unionclass
    else:
      unionclass = None
    if unionclass:
      if unionclass.subtypes.owner:
        result_type = unionclass.subtypes.owner()
        if result_type:
          return result_type
      result_type = UnionType(
        unionclass.subtypes,
        unionclass.style,
        unionclass.discriminator_key,
        unionclass.name,
        AnnotatedType.unpack(type_)[0].to_typing())
      result_type.subtypes.owner = weakref.ref(result_type)
      return result_type
    return type_
