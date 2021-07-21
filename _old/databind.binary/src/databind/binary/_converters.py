
import abc
import contextlib
import struct
from typing import Any, BinaryIO, Iterable, Iterator, Generator, Tuple, Type
from databind.core import (
  enumerate_fields,
  datamodel,
  Context,
  Converter,
  Registry,
)
from ._types import all_plain_types, get_format_for_type


class EofError(Exception):
  pass


class BufferedBinaryStream:

  def __init__(self, stream: BinaryIO) -> None:
    self._stream = stream
    self._buffer = b''

  @contextlib.contextmanager
  def try_read(self, n: int) -> Iterator[bytes]:
    data = self.read(n)
    try:
      yield data
    except:
      self.recall(data)
      raise

  def read(self, n: int) -> bytes:
    data = self._buffer[:n]
    self._buffer = self._buffer[n:]
    if len(data) >= n:
      return data
    data = data + self._stream.read(n - len(data))
    if len(data) < n:
      self.recall(data)
      raise EofError(f'running {n - len(data)} bytes short')
    return data

  def recall(self, data: bytes) -> None:
    self._buffer = data + self._buffer


class _BinaryConverter(Converter):

  @abc.abstractmethod
  def get_format_parts(self, context: Context) -> Iterable[Tuple[str, Any]]:
    pass


class PlainTypeConverter(_BinaryConverter):

  def get_format_parts(self, context: Context):
    yield get_format_for_type(context.type, context.field_metadata), context.value

  def from_python(self, value: int, context: Context) -> bytes:
    fmt = get_format_for_type(context.type, context.field_metadata)
    return struct.pack(fmt, value)

  def to_python(self, value: BufferedBinaryStream, context: Context) -> int:
    fmt = get_format_for_type(context.type, context.field_metadata)
    with value.try_read(struct.calcsize(fmt)) as data:
      return struct.unpack(fmt, data)[0]


class DatamodelConverter(_BinaryConverter):

  def get_format_parts(self, context):
    for field in enumerate_fields(context.type):
      if isinstance(context.value, BufferedBinaryStream) or context.value is None:
        child_value = None
      else:
        child_value = getattr(context.value, field.name)
      child_context = context.child(field.name, field.type, child_value, field.metadata)
      converter = child_context.get_converter()
      yield from converter.get_format_parts(child_context)

  def from_python(self, value: Any, context: Context) -> bytes:
    format_parts, values = zip(*self.get_format_parts(context))
    return struct.pack(''.join(format_parts), *values)

  def to_python(self, value: BufferedBinaryStream, context: Context) -> Any:
    format_parts, _ = zip(*self.get_format_parts(context))
    fmt = ''.join(format_parts)
    with value.try_read(struct.calcsize(fmt)) as data:
      values = struct.unpack(fmt, data)
      # TODO(NiklasRosenstein): Unpack nested datamodels.
      return context.type(*values)


def register_binary_converters(registry: Registry) -> None:
  for type_ in all_plain_types:
    registry.register_converter(type_, PlainTypeConverter())
  registry.register_converter(datamodel, DatamodelConverter())
