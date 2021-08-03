
import typing as t
from databind.core.types.types import ConcreteType

import nr.preconditions as preconditions

from databind.core.types.types import BaseType
from databind.core.mapper.converter import Converter, ConverterNotFound, ConverterProvider, Direction


class SimpleModule(ConverterProvider):
  """
  A module that you can register de-/serializers to and even other submodules. Only de-/serializers
  for concrete types can be registered in a #SimpleModule. Submodules are tested in the reversed
  order that they were registered.
  """

  def __init__(self, name: str = None) -> None:
    self.__name = name
    self.__converters_by_type: t.Dict[Direction, t.Dict[t.Type, Converter]] = {
      Direction.deserialize: {}, Direction.serialize: {}}
    self.__converter_providers: t.List[ConverterProvider] = []

  def __repr__(self):
    return f"<{type(self).__name__} {self.__name + ' ' if self.__name else ''}at {hex(id(self))}>"

  def add_converter_provider(self, provider: ConverterProvider) -> None:
    preconditions.check_instance_of(provider, ConverterProvider)  # type: ignore
    self.__converter_providers.append(provider)

  def add_converter_for_type(self, type_: t.Type, converter: Converter, direction: Direction = None) -> None:
    preconditions.check_instance_of(type_, type)
    preconditions.check_instance_of(converter, Converter)  # type: ignore
    if direction is not None:
      preconditions.check_instance_of(direction, Direction)
      self.__converters_by_type[direction][type_] = converter
    else:
      self.__converters_by_type[Direction.deserialize][type_] = converter
      self.__converters_by_type[Direction.serialize][type_] = converter

  def get_converter(self, type_: BaseType, direction: Direction) -> Converter:
    preconditions.check_instance_of(type_, BaseType)  # type: ignore
    if isinstance(type_, ConcreteType) and type_.type in self.__converters_by_type[direction]:
      return self.__converters_by_type[direction][type_.type]
    elif type(type_) in self.__converters_by_type[direction]:
      return self.__converters_by_type[direction][type(type_)]
    for module in reversed(self.__converter_providers):
      try:
        return module.get_converter(type_, direction)
      except ConverterNotFound:
        pass  # intentional
    raise ConverterNotFound(type_, direction)
