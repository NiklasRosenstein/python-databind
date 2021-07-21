
from typing import *
import sys

_T = TypeVar('_T')

if sys.version_info >= (3, 10):
    @overload
    def dataclass(__cls: Type[_T]) -> Type[_T]: ...
    @overload
    def dataclass(__cls: None) -> Callable[[Type[_T]], Type[_T]]: ...
    @overload
    def dataclass(
        *,
        init: bool = ...,
        repr: bool = ...,
        eq: bool = ...,
        order: bool = ...,
        unsafe_hash: bool = ...,
        frozen: bool = ...,
        match_args: bool = ...,
        kw_only: bool = ...,
        slots: bool = ...,
    ) -> Callable[[Type[_T]], Type[_T]]: ...

elif sys.version_info >= (3, 8):
    # cls argument is now positional-only
    @overload
    def dataclass(__cls: Type[_T]) -> Type[_T]: ...
    @overload
    def dataclass(__cls: None) -> Callable[[Type[_T]], Type[_T]]: ...
    @overload
    def dataclass(
        *, init: bool = ..., repr: bool = ..., eq: bool = ..., order: bool = ..., unsafe_hash: bool = ..., frozen: bool = ...
    ) -> Callable[[Type[_T]], Type[_T]]: ...

else:
    @overload
    def dataclass(_cls: Type[_T]) -> Type[_T]: ...
    @overload
    def dataclass(_cls: None) -> Callable[[Type[_T]], Type[_T]]: ...
    @overload
    def dataclass(
        *, init: bool = ..., repr: bool = ..., eq: bool = ..., order: bool = ..., unsafe_hash: bool = ..., frozen: bool = ...
    ) -> Callable[[Type[_T]], Type[_T]]: ...

# NOTE: Actual return type is 'Field[_T]', but we want to help type checkers
# to understand the magic that happens at runtime.
if sys.version_info >= (3, 10):
    @overload  # `default` and `default_factory` are optional and mutually exclusive.
    def field(
        *,
        default: _T,
        init: bool = ...,
        repr: bool = ...,
        hash: Optional[bool] = ...,
        compare: bool = ...,
        metadata: Optional[Mapping[str, Any]] = ...,
        kw_only: bool = ...,
        annotations: Optional[List[Any]] = ...,
    ) -> _T: ...
    @overload
    def field(
        *,
        default_factory: Callable[[], _T],
        init: bool = ...,
        repr: bool = ...,
        hash: Optional[bool] = ...,
        compare: bool = ...,
        metadata: Optional[Mapping[str, Any]] = ...,
        kw_only: bool = ...,
        annotations: Optional[List[Any]] = ...,
    ) -> _T: ...
    @overload
    def field(
        *,
        init: bool = ...,
        repr: bool = ...,
        hash: Optional[bool] = ...,
        compare: bool = ...,
        metadata: Optional[Mapping[str, Any]] = ...,
        kw_only: bool = ...,
        annotations: Optional[List[Any]] = ...,
    ) -> Any: ...

else:
    @overload  # `default` and `default_factory` are optional and mutually exclusive.
    def field(
        *,
        default: _T,
        init: bool = ...,
        repr: bool = ...,
        hash: Optional[bool] = ...,
        compare: bool = ...,
        metadata: Optional[Mapping[str, Any]] = ...,
        annotations: Optional[List[Any]] = ...,
    ) -> _T: ...
    @overload
    def field(
        *,
        default_factory: Callable[[], _T],
        init: bool = ...,
        repr: bool = ...,
        hash: Optional[bool] = ...,
        compare: bool = ...,
        metadata: Optional[Mapping[str, Any]] = ...,
        annotations: Optional[List[Any]] = ...,
    ) -> _T: ...
    @overload
    def field(
        *,
        init: bool = ...,
        repr: bool = ...,
        hash: Optional[bool] = ...,
        compare: bool = ...,
        metadata: Optional[Mapping[str, Any]] = ...,
        annotations: Optional[List[Any]] = ...,
    ) -> Any: ...
