
from databind.core import Registry
from ._converters import register_binary_converters

registry = Registry(None)
register_binary_converters(registry)

