from databind.core.converter import Converter
from databind.core.settings import ClassDecoratorSetting
from typing_extensions import Protocol

from databind.json.direction import Direction


class _JsonConverterFactor(Protocol):
    def __call__(self, direction: Direction) -> Converter:
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

    class MyCustomConverter(Converter):
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

    def __init__(self, factory: _JsonConverterFactor) -> None:
        super().__init__()
        self.factory = factory
