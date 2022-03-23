
import abc
import bisect
import collections
import dataclasses
import sys
import textwrap
import types
import typing as t
import typing_extensions as te
import warnings

from .types import BaseType, ConcreteType, ListType, SetType, MapType, OptionalType, ImplicitUnionType
from .utils import type_repr, unpack_type_hint, find_generic_bases, _ORIGIN_CONVERSION

# has_pep585_generics = not (sys.version_info < (3, 9))
# has_pep604_union_types = not (sys.version_info < (3, 10))


@dataclasses.dataclass
class TypeHintAdapterError(Exception):
  adapter: 'TypeHintAdapter'
  message: str
  causes: t.List['TypeHintAdapterError'] = dataclasses.field(default_factory=list)

  def __str__(self) -> str:
    parts = [self.message] + [str(c) for c in self.causes]
    return '\n'.join(parts)


@dataclasses.dataclass
class TypeContext:
  """ Tracking context for type adaptation. """

  root_adapter: 'TypeHintAdapter'
  globals_: t.Optional[t.Mapping[str, t.Any]] = None
  locals: t.Optional[t.Mapping[str, t.Any]] = None
  type_vars: t.Optional[t.Mapping[t.TypeVar, t.Any]] = None
  _source: t.Any = None

  def adapt_type_hint(self, type_hint: t.Any) -> BaseType:
    return self.root_adapter.adapt_type_hint(type_hint, self.with_type_vars_of(type_hint))

  def resolve_forward_reference(self, forward_ref: t.Union[str, t.ForwardRef]) -> t.Any:
    if isinstance(forward_ref, str):
      forward_ref = t.ForwardRef(forward_ref)
    # FIXME (@NiklasRosenstein): Relying on internal typing API here.
    if sys.version_info < (3, 9):
      return forward_ref._evaluate(self.globals_, self.locals)  # type: ignore
    else:
      return forward_ref._evaluate(self.globals_, self.locals, frozenset())  # type: ignore

  def resolve_type_var(self, type_variable: t.TypeVar) -> t.Any:
    try:
      return (self.type_vars or {})[type_variable]
    except KeyError:
      raise RuntimeError(f'cannot resolve {type_variable!r} in {self._source!r}')

  def apply_type_vars(self, type_hint: t.Any) -> t.Any:
    if self.type_vars is None:
      return type_hint
    if not hasattr(type_hint, '__origin__') and hasattr(type_hint, '__parameters__'):
      args = tuple(self.type_vars.get(k) for k in type_hint.__parameters__)
      if args:
        return type_hint[args]
    return type_hint

  def with_scope_of(self, type_hint: t.Any) -> 'TypeContext':
    """ Tries to assume the scope (i.e. globals and locals) of the type given with *type_hint* and returns a new
    type context. If no scope can be identified for the type hint, the returned context will not contain a scope.
    """

    if hasattr(type_hint, '__origin__'):
      type_hint = type_hint.__origin__

    if isinstance(type_hint, type):
      module = sys.modules.get(type_hint.__module__)
    else:
      module = None

    return TypeContext(
      root_adapter=self.root_adapter,
      globals_=vars(module) if module else self.globals_,
      locals=None,
      type_vars=self.type_vars,
      _source=type_hint,
    )

  def with_type_vars_of(self, type_hint: t.Any, l: bool = False) -> 'TypeContext':
    """ Extracts assigned type paremtrizations and carries them forward in a new type context returned by this
    function. """

    def _resolve_type_var(tv: t.TypeVar) -> t.Any:
      if self.type_vars and tv in self.type_vars:
        return self.type_vars[tv]
      elif isinstance(tv.__bound__, (str, t.ForwardRef)):
        return self.resolve_forward_reference(tv.__bound__)  # type: ignore[unreachable]
      elif isinstance(tv.__bound__, str):
        return self.resolve_forward_reference(tv.__bound__)  # type: ignore[unreachable]
      elif tv.__bound__:
        return tv.__bound__
      else:
        return t.Any

    def _evaluate(a: t.Any) -> t.Any:
      if isinstance(a, t.TypeVar):
        return _resolve_type_var(a)
      elif isinstance(a, t.ForwardRef):
        return self.resolve_forward_reference(a)
      return a

    if hasattr(type_hint, '__origin__') and hasattr(type_hint.__origin__, '__parameters__'):
      args = [_evaluate(a) for a in type_hint.__args__]
      type_hint = type_hint.__origin__
      type_vars = dict(zip(type_hint.__parameters__, args))

    elif hasattr(type_hint, '__parameters__'):
      type_vars = {p: _resolve_type_var(p) for p in type_hint.__parameters__}

    else:
      type_vars = {}

    if hasattr(type_hint, '__orig_bases__'):
      scoped = self.with_scope_of(type_hint)
      for base in type_hint.__orig_bases__:
        type_vars = {**(scoped.with_type_vars_of(base).type_vars or {}), **type_vars}

    if self.type_vars:
      type_vars = {**self.type_vars, **type_vars}

    return TypeContext(
      root_adapter=self.root_adapter,
      globals_=self.globals_,
      locals=self.locals,
      type_vars=type_vars,
      _source=type_hint,
    )


class TypeHintAdapter(abc.ABC):

  Error = TypeHintAdapterError

  @abc.abstractmethod
  def adapt_type_hint(self, type_hint: t.Any, context: TypeContext) -> BaseType: ...


class DefaultTypeHintAdapter(TypeHintAdapter):
  """
  Adapter for all the supported standard #typing type hints.
  """

  def adapt_type_hint(self, type_hint: t.Any, context: TypeContext) -> BaseType:
    generic, args = unpack_type_hint(type_hint)
    from_typing = context.adapt_type_hint

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
          return OptionalType(from_typing(t.Union[tuple(x for x in args if x is not type(None))]))  # type: ignore
        else:
          return ImplicitUnionType(tuple(from_typing(a) for a in args))
      elif hasattr(te, 'Annotated') and generic == te.Annotated and len(args) >= 2:  # type: ignore
        type_ = from_typing(args[0])
        type_.annotations += args[1:]
        return from_typing(type_)

    if isinstance(type_hint, str):
      return from_typing(context.resolve_forward_reference(type_hint))

    if isinstance(type_hint, type):
      return from_typing(ConcreteType(type_hint))

    if isinstance(type_hint, BaseType):
      return type_hint

    if isinstance(type_hint, t.TypeVar):
      resolved = context.resolve_type_var(type_hint)
      return context.with_scope_of(resolved).adapt_type_hint(resolved)

    if generic is not None and isinstance(generic, type):  # Probably a subclass of typing.Generic
      return context.root_adapter.adapt_type_hint(generic, context)

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

  def adapt_type_hint(self, type_hint: t.Any, context: TypeContext) -> BaseType:
    errors = []
    for _priority_group, adapters in self._ordered:
      for adapter in adapters:
        try:
          type_hint = adapter.adapt_type_hint(type_hint, context)
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
    raise TypeHintAdapterError(self, 'no available adapter matched\n' + summary, errors)
