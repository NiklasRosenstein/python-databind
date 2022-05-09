from __future__ import annotations

import abc
import logging
import typing as t

import typeapi
from nr.util.exceptions import safe_str

if t.TYPE_CHECKING:
    from databind.core.context import Context

logger = logging.getLogger(__name__)


class Converter(abc.ABC):
    """Interface for converting a value from one representation to another."""

    @abc.abstractmethod
    def convert(self, ctx: Context) -> t.Any:
        """Convert the value in *ctx* to another value.

        Argument:
          ctx: The conversion context that contains the value, datatype, settings, location and allows you to
            recursively continue the conversion process for sub values.
        Raises:
          NotImplementedError: If the converter does not support the conversion for the given context.
          NoMatchingConverter: If the converter is delegating to other converters, to point out that none
            of its delegates can convert the value.
        Returns:
          The new value.
        """


class Module(Converter):
    """A module is a collection of #Converter#s."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.converters: t.List[Converter] = []

    def __repr__(self) -> str:
        return f"Module({self.name!r})"

    def register(self, converter: Converter) -> None:
        assert isinstance(converter, Converter), converter
        self.converters.append(converter)

    def convert(self, ctx: Context) -> t.Any:
        errors: t.List[t.Tuple[Converter, Exception]] = []
        for converter in self.converters:
            try:
                return converter.convert(ctx)
            except NotImplementedError as exc:
                errors.append((converter, exc))
            except NoMatchingConverter as exc:
                errors.extend(exc.errors)
        raise NoMatchingConverter(self, ctx, errors)


class ConversionError(Exception):
    """For any errors that occur during conversion."""

    def __init__(
        self,
        origin: Converter,
        context: Context,
        message: str,
        errors: t.Optional[t.List[t.Tuple[Converter, Exception]]] = None,
    ) -> None:
        self.origin = origin
        self.context = context
        self.message = message
        self.errors = errors or []

    @safe_str
    def __str__(self) -> str:
        import textwrap

        from databind.core.context import format_context_trace

        message = f'{self.message}\nConversion trace:\n{textwrap.indent(format_context_trace(self.context), "  ")}'
        if self.errors:
            message += "\nThe following errors have been reported by converters:"
            for converter, exc in self.errors:
                if str(exc):
                    message += f"\n  {converter}: {exc}"
        return message

    @staticmethod
    def expected(
        origin: Converter,
        ctx: Context,
        types: t.Union[t.Type, t.Sequence[t.Type]],
        got: t.Optional[t.Type] = None,
    ) -> ConversionError:
        if not isinstance(types, t.Sequence):
            types = (types,)
        expected = "|".join(typeapi.type_repr(t) for t in types)
        got = type(ctx.value) if got is None else got
        return ConversionError(origin, ctx, f"expected {expected}, got {typeapi.type_repr(got)} instead")


class NoMatchingConverter(ConversionError):
    """If no converter matched to convert the value and datatype in the context."""

    def __init__(self, origin: Converter, context: Context, errors: t.List[t.Tuple[Converter, Exception]]) -> None:
        super().__init__(origin, context, f"no applicable converter found for {context.datatype}", errors)
