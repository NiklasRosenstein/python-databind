
import typing as t
from databind.core.types.types import ConcreteType

from databind.core.types.types import BaseType
from databind.core.mapper.converter import Converter, ConverterProvider, Direction


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
    assert isinstance(provider, ConverterProvider), provider
    self.__converter_providers.append(provider)

  def add_converter_for_type(self, type_: t.Type, converter: Converter, direction: Direction = None) -> None:
    assert isinstance(type_, type), type_
    assert isinstance(converter, Converter), converter

    if direction is not None:
      assert isinstance(direction, Direction)
      self.__converters_by_type[direction][type_] = converter
    else:
      self.__converters_by_type[Direction.deserialize][type_] = converter
      self.__converters_by_type[Direction.serialize][type_] = converter

  def get_converters(self, type_: BaseType, direction: Direction) -> t.Iterable[Converter]:
    assert isinstance(type_, BaseType), type_

    if isinstance(type_, ConcreteType) and type_.type in self.__converters_by_type[direction]:
      yield self.__converters_by_type[direction][type_.type]
    elif type(type_) in self.__converters_by_type[direction]:
      yield self.__converters_by_type[direction][type(type_)]
    for module in reversed(self.__converter_providers):
      yield from module.get_converters(type_, direction)
