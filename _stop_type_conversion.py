
  # IModule
  def convert_type_hint(self, type_hint: t.Any, recurse: ITypeHintConverter) -> BaseType:

    if isinstance(type_, ConcreteType):
      # Type's for which we have a serializer or deserializer do not require adaptation.
      # The background here is that there can be #ConcreteType's that wrap a @dataclass
      # which would be adapter to an #ObjectType by the #DataclassAdapter unless we catch
      # that there is an explicit converter registered to handle that special case.
      has_converter = False
      try: self.get_converter(type_, Direction.deserialize)
      except ConverterNotFound: pass
      else: has_converter = True
      if not has_converter:
        try: self.get_converter(type_, Direction.serialize)
        except ConverterNotFound: pass
        else: has_converter = True
        pass

      if has_converter:
        return type_

    # Apply the type adaptation recursively on all nested types.
    parent_method = super().adapt_type_hint
    def visitor(current_type: BaseType) -> BaseType:
      return parent_method(current_type, adapter or self)
    return type_.visit(visitor)
