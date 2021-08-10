
import abc
import bisect
import collections
import dataclasses
import textwrap
import typing as t
import typing_extensions as te
import warnings

from .types import BaseType, ConcreteType, ListType, SetType, MapType, OptionalType, ImplicitUnionType
from .utils import type_repr, unpack_type_hint, find_generic_bases, _ORIGIN_CONVERSION


@dataclasses.dataclass
class TypeHintAdapterError(Exception):
  adapter: 'TypeHintAdapter'
  message: str


class TypeHintAdapter(abc.ABC):

  Error = TypeHintAdapterError

  def adapt_type_hint(self, type_hint: t.Any, recurse: t.Optional['TypeHintAdapter'] = None) -> BaseType:
    return self._adapt_type_hint_impl(type_hint, recurse or self)

  @abc.abstractmethod
  def _adapt_type_hint_impl(self, type_hint: t.Any, recurse: 'TypeHintAdapter') -> BaseType: ...

class DefaultTypeHintAdapter(TypeHintAdapter):
  """
  Adapter for all the supported standard #typing type hints.
  """

  def _adapt_type_hint_impl(self, type_hint: t.Any, recurse: TypeHintAdapter) -> BaseType:
    generic, args = unpack_type_hint(type_hint)
    from_typing = lambda th: recurse._adapt_type_hint_impl(th, recurse)

    # Support custom subclasses of typing generic aliases (e.g. class MyList(t.List[int])
    # or class MyDict(t.Mapping[K, V])). If we find a type like that, we keep a reference
    # to it in "python_type" so we know what we need to construct during deserialization.
    # NOTE (@NiklasRosenstein): We only support a single generic base.
    python_type: t.Optional[t.Type] = None
    generic_bases = find_generic_bases(type_hint)
    # Filter down to supported generic bases.
    generic_bases = [b for b in generic_bases if b.__origin__ in _ORIGIN_CONVERSION]
    if len(generic_bases) == 1:
      python_type = generic
      generic, args = unpack_type_hint(generic_bases[0])
    elif len(generic_bases) > 1:
      warnings.warn(f'Found multiple supported generic bases for `{type_repr(type_hint)}`, '
        f'can not decide which to pick. Generic bases found: {generic_bases}', UserWarning)

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

    raise TypeHintAdapterError(self, f'unsupported type hint {type_hint!r}')


class ChainTypeHintAdapter(TypeHintAdapter):
  """
  Delegates to a chain of #TypeHintAdapter#s. Each adapter can have a priority. Aonverters
  passed to the construct will have priority 0 and a higher priority indicates that the adapter
  will be used checked first.
  """

  def __init__(self, *adapters: TypeHintAdapter) -> None:
    self._priorities: t.Dict[int, t.List[TypeHintAdapter]] = collections.defaultdict(list)
    self._priorities[0] = list(adapters)
    self._ordered: t.List[t.Tuple[int, t.List[TypeHintAdapter]]] = list(self._priorities.items())
    self._ordered.sort()
    self._stop_conditions: t.List[t.Callable[[BaseType], bool]] = []

  def add_type_hint_adapter_stop_condition(self, condition: t.Callable[[BaseType], bool]) -> None:
    """
    Add a stop condition that will determine if a #BaseType that was already adapter from another
    #TypeHintAdapter will continue to be adapted by the remaining adapters in the chain. If no conditions
    are registered, the default response will be #True.
    """

    self._stop_conditions.append(condition)

  def add_type_hint_adapter(self, adapter: TypeHintAdapter, priority: int = 0) -> None:
    """
    Register a new adapter. The default priority is 0. Within the same priority group, a adapter
    will always be appended at the end of the list such that it will be checked last in the priority
    group.
    """

    priority_group_exists = priority in self._priorities
    self._priorities[priority].append(adapter)
    if not priority_group_exists:
      item = (priority, self._priorities[priority])
      self._ordered.insert(bisect.bisect(self._ordered, item), item)

  def _adapt_type_hint_impl(self, type_hint: t.Any, recurse: TypeHintAdapter) -> BaseType:
    errors = []
    for _priority_group, adapters in self._ordered:
      for adapter in adapters:
        try:
          type_hint = adapter._adapt_type_hint_impl(type_hint, recurse)
        except TypeHintAdapterError as exc:
          errors.append(exc)
        if isinstance(type_hint, BaseType) and any(x(type_hint) for x in self._stop_conditions):
          return type_hint
    if isinstance(type_hint, BaseType):
      return type_hint
    if not errors:
      raise TypeHintAdapterError(self, 'no adapters registered')
    summary = '\n'.join(f'{str(exc.adapter)}: {exc.message}' for exc in errors)
    summary = textwrap.indent(summary, '  ')
    raise TypeHintAdapterError(self, 'no available adapter matched\n' + summary)
