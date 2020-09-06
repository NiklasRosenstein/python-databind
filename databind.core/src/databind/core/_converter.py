
import abc
import contextlib
from dataclasses import dataclass as _dataclass
from typing import Any, Dict, Generator, Generic, List, Mapping, Optional, Type, TypeVar, Union
from ._datamodel import (
  BaseMetadata,
  FieldMetadata,
  ModelMetadata,
  UnionMetadata,
  datamodel,
  uniontype,
)
from ._locator import Locator
from ._typing import type_repr
from .utils import ChainDict

T = TypeVar('T')

__all__ = [
  'ConversionError',
  'ConversionTypeError',
  'ConversionValueError',
  'Context',
  'Converter',
  'UnknownTypeError',
  'Registry',
]


@_dataclass
class ConversionError(Exception):
  context: 'Context'
  message: str

  def __str__(self):
    return '{}: {}'.format(self.context.locator, self.message)


class ConversionTypeError(ConversionError, TypeError):
  pass


class ConversionValueError(ConversionError, ValueError):
  pass


@_dataclass
class Context:
  """
  The context contains data relevant during value conversion, such as metadata coming from
  union types, data models and fields. The context represents a tree, where every element in
  that tree represents a value in the structured data that is being converted.
  """

  parent: Optional['Context']
  registry: 'Registry'
  locator: Locator
  type: Type
  value: Any
  field_metadata: Optional[FieldMetadata]

  @classmethod
  def new(cls, registry: 'Registry', type_: Type, value: Any, field_metadata: FieldMetadata=None) -> 'Context':
    return cls(None, registry, Locator([]), type_, value, field_metadata)

  def fork(
    self,
    type_: Type,
    value: Any,
    field_metadata: Optional[FieldMetadata] = NotImplemented,
  ) -> 'Context':
    """
    Create a fork in the context tree, re-using the same locator and parent but allowing to
    change the type and value, and optionally the field metadata.
    """

    if field_metadata is NotImplemented:
      field_metadata = self.field_metadata

    return Context(self.parent, self.registry, self.locator, type_, value, field_metadata)

  def child(
    self,
    key: Union[int, str],
    type_: Type,
    value: Any,
    field_metadata: FieldMetadata=None
  ) -> 'Context':
    """
    Create a new child node in the context tree, advancing to the next sub-structure from the
    current value.
    """

    return Context(self, self.registry, self.locator.push(key), type_, value, field_metadata)

  def get_converter(self) -> 'Converter':
    return self.registry.get_converter(self.type)

  def from_python(self) -> Any:
    return self.get_converter().from_python(self.value, self)

  def to_python(self) -> Any:
    return self.get_converter().to_python(self.value, self)

  def type_error(self, message: str) -> ConversionTypeError:
    return ConversionTypeError(self, message)

  def value_error(self, message: str) -> ConversionValueError:
    return ConversionValueError(self, message)

  @contextlib.contextmanager
  def coerce_errors(self) -> Generator[None, None, None]:
    """
    A context manager that catches #ValueError and #TypeError exceptions to convert them to the
    corresponding #ConversionTypeError and #ConversionValueError types.
    """

    try:
      yield
    except ValueError as exc:
      raise self.value_error(str(exc))
    except TypeError as exc:
      raise self.type_error(str(exc))


class Converter(Generic[T], metaclass=abc.ABCMeta):
  """
  Abstract base class that convert from and to a Python datatype.
  """

  @abc.abstractmethod
  def from_python(self, value: T, context: Context) -> Any:
    pass

  @abc.abstractmethod
  def to_python(self, value: Any, context: Context) -> T:
    pass


class UnknownTypeError(TypeError):
  pass


class Registry:
  """
  The registry is what maps data types and type hints to #Converter implementations. Types that
  are decorated with #@uniontype() or #@datamodel() are handled special in that they must be
  associated with the respective decorator function.
  """

  def __init__(self, parent: Optional['Registry']) -> None:
    self.parent = parent
    self._mapping: Dict[Any, Converter] = {}
    self._type_options: Dict[Any, Dict[str, Any]] = {}

  @property
  def root(self) -> 'Registry':
    if not self.parent:
      return self
    return self.parent.root

  def register_converter(self, type_: Any, converter: Converter, overwrite: bool = False) -> None:
    """
    Registers a convert for the specified Python type or type hint.
    """

    old = type_
    type_ = normalize_type(type_, keep_parametrized=True)
    if type_ in self._mapping and not overwrite:
      raise RuntimeError(f'converter for {type_repr(type_)} already registered')
    if not isinstance(converter, Converter):
      raise TypeError(f'expected Converter, got {type_repr(type(converter))}')
    self._mapping[type_] = converter

  def update_options(self, type_: Any, options: Dict[str, Any]) -> None:
    """
    Registers options with the specified Python type or type hint. Existing options are
    merged, with the options specified to this method taking precedence.
    """

    self._type_options.setdefault(type_, {}).update(options)

  def set_option(self, type_: Any, option_name: str, value: Any) -> None:
    """
    Set a specific option.
    """

    self._type_options.setdefault(type_, {})[option_name] = value

  def get_options(self, type_: Any) -> Mapping[str, Any]:
    """
    Returns a mapping that contains all options for the specified type or type hint, taking
    options defined on the parent #Registry into account.

    Note that this does not respect type inheritance.
    """

    options: Mapping[str, Any] = self._type_options.get(type_, {})
    if self.parent:
      options = ChainDict(options, self.parent.get_options(type_))
    return options

  def get_option(self, type_: Any, option_name: str, default: Any = None) -> Any:
    """
    Return a specific option associated with the specified type or type hint.
    """

    return self.get_options(type_).get(option_name, default)

  def get_converter(self, type_: Type) -> Converter:
    """
    Return a converter registered for this type or type hint. If there is no immediate match
    for the type, it will be normalized using #normalize_type().
    """

    if type_ in self._mapping:
      return self._mapping[type_]

    if self.parent:
      try:
        return self.parent.get_converter(type_)
      except UnknownTypeError:
        pass

    # Try base classes.
    for base in getattr(type_, '__bases__', ()):
      try:
        return self.get_converter(base)
      except UnknownTypeError:
        pass

    normalized = normalize_type(type_, keep_parametrized=False)
    if normalized != type_:
      return self.get_converter(normalized)

    raise UnknownTypeError(f'no converter found for type {type_repr(type_)}')

  def make_context(self, type_: Type, value: Any, field_metadata: FieldMetadata = None) -> Any:
    return Context.new(self, type_, value, field_metadata)


def normalize_type(type_: Any, keep_parametrized: bool) -> Type:
  """
  Normalizes a Python type or type hint. For type hints, this will return the `__origin__`.
  If *keep_parametrized* is `True`, then the `__origin__` will only be returned if the type
  hint is not parametrized (i.e. still generic).
  """

  # Map type's decoreated with uniontype/datamodel to the respective functions.
  metadata = BaseMetadata.for_type(type_)
  if isinstance(metadata, UnionMetadata):
    type_ = uniontype
  elif isinstance(metadata, ModelMetadata):
    type_ = datamodel

  # Resolve type hints to the original annotated form.
  # NOTE: In Python 3.6, Dict.__origin__ is None whereas in Python 3.7 it is dict.
  if getattr(type_, '__origin__', None) and (not keep_parametrized or type_.__parameters__):
    type_ = type_.__origin__

  return type_
