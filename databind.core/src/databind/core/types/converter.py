
import abc
import bisect
import collections
import dataclasses
import textwrap
import typing as t
import typing_extensions as te

from .types import BaseType, ConcreteType, ListType, SetType, MapType, OptionalType, ImplicitUnionType
from .utils import unpack_type_hint, find_generic_bases, _ORIGIN_CONVERSION


@dataclasses.dataclass
class TypeHintConversionError(Exception):
  converter: 'TypeHintConverter'
  message: str


class TypeHintConverter(abc.ABC):

  def __call__(self, type_hint: t.Any) -> 'BaseType':
    return self.convert_type_hint(type_hint, self)

  @abc.abstractmethod
  def convert_type_hint(self, type_hint: t.Any, recurse: 'TypeHintConverter') -> 'BaseType': ...


class DefaultTypeHintConverter(TypeHintConverter):
  """
  Converter for all the supported standard #typing type hints.
  """

  def convert_type_hint(self, type_hint: t.Any, recurse: 'TypeHintConverter') -> 'BaseType':
    generic, args = unpack_type_hint(type_hint)
    from_typing = lambda th: recurse.convert_type_hint(th, recurse)

    # Support custom subclasses of typing generic aliases (e.g. class MyList(t.List[int])
    # or class MyDict(t.Mapping[K, V])). If we find a type like that, we keep a reference
    # to it in "python_type" so we know what we need to construct during deserialization.
    # NOTE (@NiklasRosenstein): We only support a single generic base.
    python_type: t.Optional[t.Type] = None
    generic_bases = find_generic_bases(type_hint)
    if len(generic_bases) == 1:
      python_type = generic
      generic, args = unpack_type_hint(generic_bases[0])

    if generic is not None:
      generic = _ORIGIN_CONVERSION.get(generic, generic)
      if generic == t.Any:
        return ConcreteType(object)
      elif generic == t.List and len(args) == 1:
        return ListType(from_typing(args[0]), python_type or list)
      elif generic == t.Set and len(args) == 1:
        return SetType(from_typing(args[0]), python_type or set)
      elif generic in (t.Dict, t.Mapping, t.MutableMapping) and len(args) == 2:
        return MapType(from_typing(args[0]), from_typing(args[1]), python_type or generic)
      elif (generic == t.Optional and len(args) == 1) or (generic == t.Union and None in args and len(args) == 2):  # type: ignore
        if len(args) == 1:
          return OptionalType(from_typing(args[0]))
        elif len(args) == 2:
          return OptionalType(from_typing(next(x for x in args if x is not None)))
        else:
          raise ValueError(f'unexpected args for {generic}: {args}')
      elif generic == t.Union and len(args) > 0:
        if len(args) == 1:
          return from_typing(args[0])
        elif type(None) in args:
          return OptionalType(from_typing(t.Union[tuple(x for x in args if x is not type(None))]))
        else:
          return ImplicitUnionType(tuple(from_typing(a) for a in args))
      elif hasattr(te, 'Annotated') and generic == te.Annotated and len(args) >= 2:  # type: ignore
        type_ = from_typing(args[0])
        type_.annotations += args[1:]
        return type_

    if isinstance(type_hint, type):
      return ConcreteType(type_hint)

    raise TypeHintConversionError(self, f'unsupported type hint {type_hint!r}')


class ChainTypeHintConverter(TypeHintConverter):
  """
  Delegates to a chain of #ITypeHintConverter#s. Each converter can have a priority. Converters
  passed to the construct will have priority 0 and a higher priority indicates that the converter
  will be used checked first.
  """

  def __init__(self, *converters: TypeHintConverter) -> None:
    self._priorities: t.Dict[int, t.List[TypeHintConverter]] = collections.defaultdict(list)
    self._priorities[0] = list(converters)
    self._ordered: t.List[t.Tuple[int, t.List[TypeHintConverter]]] = list(self._priorities.items())
    self._ordered.sort()

  def register(self, converter: TypeHintConverter, priority: int = 0) -> None:
    """
    Register a new converter. The default priority is 0. Within the same priority group, a converter
    will always be appended at the end of the list such that it will be checked last in the priority
    group.
    """

    priority_group_exists = priority in self._priorities
    self._priorities[priority].append(converter)
    if not priority_group_exists:
      item = (priority, self._priorities[priority])
      self._ordered.insert(bisect.bisect(self._ordered, item), item)

  def convert_type_hint(self, type_hint: t.Any, recurse: 'TypeHintConverter') -> 'BaseType':
    errors = []
    for _priority_group, converters in self._ordered:
      for converter in converters:
        try:
          type_hint = converter.convert_type_hint(type_hint, recurse)
        except TypeHintConversionError as exc:
          errors.append(exc)
    if isinstance(type_hint, BaseType):
      return type_hint
    if not errors:
      raise TypeHintConversionError(self, 'no converters registered')
    summary = '\n'.join(f'{str(exc.converter)}: {exc.message}' for exc in errors)
    summary = textwrap.indent(summary, '  ')
    raise TypeHintConversionError(self, 'no available converter matched\n' + summary)



