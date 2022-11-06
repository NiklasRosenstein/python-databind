import typing as t

import typing_extensions as te
from databind.core.converter import Converter
from databind.core.settings import ClassDecoratorSetting


class ConverterSupplier(te.Protocol):
    def __call__(self) -> Converter:
        ...


class JsonConverter(ClassDecoratorSetting):
    """Use this setting to decorate a class or to annotate a type hint to inform the JSON module to use the
    specified convert when deserialize the type instead of any converter that would otherwise match the type.

    Example:

    ```py
    from databind.core.converter import Converter
    from databind.json.direction import Direction
    from databind.json.settings import JsonConverter
    from typing import Any

    class MyCustomConverter(JsonConverter.Base):
        def __init__(self, direction: Direction) -> None:
            self.direction = direction
        def convert(self, ctx: Context) -> Any:
            ...

    @JsonConverter(MyCustomConverter)
    class MyCustomType:
        ...

    # Or

    Annotated[MyCustomType, JsonConverter(MyCustomConverter)]
    ```"""

    supplier: ConverterSupplier

    def __init__(self, supplier: t.Union[ConverterSupplier, Converter]) -> None:
        super().__init__()
        if isinstance(supplier, Converter):
            self.supplier = lambda: supplier
        else:
            self.supplier = supplier
