import dataclasses
import datetime
import decimal
import enum
import typing as t
import uuid

import pytest
import typeapi
import typing_extensions as te
from databind.core.converter import ConversionError, Converter
from databind.core.mapper import ObjectMapper
from databind.core.settings import Alias, ExtraKeys, Flattened, Remainder, SerializeDefaults, Strict, Union
from nr.util.date import duration

from databind.json.converters import (
    AnyConverter,
    CollectionConverter,
    DatetimeConverter,
    DecimalConverter,
    EnumConverter,
    MappingConverter,
    OptionalConverter,
    PlainDatatypeConverter,
    SchemaConverter,
    StringifyConverter,
    UnionConverter,
)
from databind.json.direction import Direction


def make_mapper(converters: t.List[Converter]) -> ObjectMapper:
    mapper = ObjectMapper()
    for converter in converters:
        mapper.module.register(converter)
    return mapper


def test_any_converter():
    mapper = make_mapper([AnyConverter()])
    assert mapper.convert("foobar", t.Any) == "foobar"
    assert mapper.convert(42, t.Any) == 42
    assert mapper.convert(t.Any, t.Any) == t.Any


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_plain_datatype_converter(direction: Direction):
    mapper = make_mapper([PlainDatatypeConverter(direction)])

    # test strict

    assert mapper.convert("foobar", str) == "foobar"
    assert mapper.convert(42, int) == 42
    with pytest.raises(ConversionError):
        assert mapper.convert("42", int)

    # test non-strict

    mapper.settings.add_global(Strict(False))
    if direction == Direction.SERIALIZE:
        with pytest.raises(ConversionError):
            assert mapper.convert("42", int)

    else:
        assert mapper.convert("42", int) == 42
        with pytest.raises(ConversionError):
            mapper.convert("foobar", int)


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_decimal_converter(direction: Direction):
    mapper = make_mapper([DecimalConverter(direction)])

    pi = decimal.Decimal("3.141592653589793")
    if direction == Direction.SERIALIZE:
        assert mapper.convert(pi, decimal.Decimal) == str(pi)

    else:
        assert mapper.convert(str(pi), decimal.Decimal) == pi
        with pytest.raises(ConversionError):
            assert mapper.convert(3.14, decimal.Decimal)
        assert mapper.convert(3.14, decimal.Decimal, settings=[Strict(False)]) == decimal.Decimal(3.14)


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_enum_converter(direction: Direction):
    mapper = make_mapper([EnumConverter(direction)])

    class Pet(enum.Enum):
        CAT = enum.auto()
        DOG = enum.auto()
        LION: te.Annotated[int, Alias("KITTY")] = enum.auto()

    if direction == Direction.SERIALIZE:
        assert mapper.convert(Pet.CAT, Pet) == "CAT"
        assert mapper.convert(Pet.DOG, Pet) == "DOG"
        assert mapper.convert(Pet.LION, Pet) == "KITTY"
    else:
        assert mapper.convert("CAT", Pet) == Pet.CAT
        assert mapper.convert("DOG", Pet) == Pet.DOG
        assert mapper.convert("KITTY", Pet) == Pet.LION

    class Flags(enum.IntEnum):
        A = 1
        B = 2

    if direction == Direction.SERIALIZE:
        assert mapper.convert(Flags.A, Flags) == 1
        assert mapper.convert(Flags.B, Flags) == 2
        with pytest.raises(ConversionError):
            assert mapper.convert(Flags.A | Flags.B, Flags)
    else:
        assert mapper.convert(1, Flags) == Flags.A
        assert mapper.convert(2, Flags) == Flags.B
        with pytest.raises(ConversionError):
            assert mapper.convert(3, Flags)


def test_optional_converter():
    mapper = make_mapper([OptionalConverter(), PlainDatatypeConverter(Direction.SERIALIZE)])
    assert mapper.convert(42, t.Optional[int]) == 42
    assert mapper.convert(None, t.Optional[int]) == None
    assert mapper.convert(42, int) == 42
    with pytest.raises(ConversionError):
        assert mapper.convert(None, int)


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_datetime_converter(direction: Direction):
    mapper = make_mapper([DatetimeConverter(direction)])

    tests = [
        (datetime.time(11, 30, 10), "11:30:10.0"),
        (datetime.date(2022, 2, 4), "2022-02-04"),
        (datetime.datetime(2022, 2, 4, 11, 30, 10), "2022-02-04T11:30:10.0"),
    ]

    for py_value, str_value in tests:
        if direction == Direction.SERIALIZE:
            assert mapper.convert(py_value, type(py_value)) == str_value
        else:
            assert mapper.convert(str_value, type(py_value)) == py_value


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_duration_converter(direction: Direction):
    mapper = make_mapper([StringifyConverter(direction, duration, duration.parse)])

    tests = [
        (duration(2, 1, 4, 0, 3), "P2Y1M4WT3H"),
    ]

    for py_value, str_value in tests:
        if direction == Direction.SERIALIZE:
            assert mapper.convert(py_value, duration) == str_value
        else:
            assert mapper.convert(str_value, duration) == py_value


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_stringify_converter(direction: Direction):
    mapper = make_mapper([StringifyConverter(direction, uuid.UUID)])

    uid = uuid.uuid4()
    if direction == Direction.SERIALIZE:
        assert mapper.convert(uid, uuid.UUID) == str(uid)
    else:
        assert mapper.convert(str(uid), uuid.UUID) == uid


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_mapping_converter(direction):
    mapper = make_mapper([AnyConverter(), MappingConverter(direction), PlainDatatypeConverter(direction)])
    assert mapper.convert({"a": 1}, t.Mapping) == {"a": 1}
    assert mapper.convert({"a": 1}, t.Mapping[str, int]) == {"a": 1}
    assert mapper.convert({"a": 1}, t.MutableMapping[str, int]) == {"a": 1}
    assert mapper.convert({"a": 1}, t.Dict[str, int]) == {"a": 1}
    with pytest.raises(ConversionError):
        assert mapper.convert(1, t.Mapping[int, str])

    K, V = t.TypeVar("K"), t.TypeVar("V")

    class CustomDict(t.Dict[K, V]):
        pass

    if direction == Direction.SERIALIZE:
        assert mapper.convert(CustomDict({"a": 1}), CustomDict[str, int]) == {"a": 1}
    else:
        assert mapper.convert({"a": 1}, CustomDict[str, int]) == CustomDict({"a": 1})

    # class FixedDict(t.Dict[int, str]):
    #   pass
    # if direction == Direction.SERIALIZE:
    #   assert mapper.convert(FixedDict({"a": 1}), FixedDict) == {"a": 1}
    # else:
    #   assert mapper.convert({"a": 1}, FixedDict) == FixedDict({"a": 1})


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_collection_converter(direction):
    mapper = make_mapper([AnyConverter(), CollectionConverter(direction), PlainDatatypeConverter(direction)])
    assert mapper.convert([1, 2, 3], t.Collection) == [1, 2, 3]
    assert mapper.convert([1, 2, 3], t.Collection[int]) == [1, 2, 3]
    assert mapper.convert([1, 2, 3], t.MutableSequence[int]) == [1, 2, 3]
    assert mapper.convert([1, 2, 3], t.List[int]) == [1, 2, 3]
    with pytest.raises(ConversionError):
        assert mapper.convert(1, t.Mapping[int, str])

    T = t.TypeVar("T")

    class CustomList(t.List[T]):
        pass

    if direction == Direction.SERIALIZE:
        assert mapper.convert(CustomList([1, 2, 3]), CustomList[int]) == [1, 2, 3]
    else:
        assert mapper.convert([1, 2, 3], CustomList[int]) == CustomList([1, 2, 3])

    # class FixedList(t.List[int]):
    #   pass
    # if direction == Direction.SERIALIZE:
    #   assert mapper.convert(FixedList([1, 2, 3]), FixedList) == [1, 2, 3]
    # else:
    #   assert mapper.convert([1, 2, 3], FixedList) == FixedList([1, 2, 3])


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_union_converter_nested(direction):
    mapper = make_mapper([UnionConverter(direction), PlainDatatypeConverter(direction)])

    hint = te.Annotated[t.Union[int, str], Union({"int": int, "str": str})]
    if direction == Direction.DESERIALIZE:
        assert mapper.convert({"type": "int", "int": 42}, hint) == 42
    else:
        assert mapper.convert(42, hint) == {"type": "int", "int": 42}


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_union_converter_best_match(direction):
    mapper = make_mapper([UnionConverter(direction), PlainDatatypeConverter(direction)])

    if direction == Direction.DESERIALIZE:
        assert mapper.convert(42, t.Union[int, str]) == 42
    else:
        assert mapper.convert(42, t.Union[int, str]) == 42


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_union_converter_keyed(direction):
    mapper = make_mapper([UnionConverter(direction), PlainDatatypeConverter(direction)])

    th = te.Annotated[t.Union[int, str], Union({"int": int, "str": str}, style=Union.KEYED)]
    if direction == Direction.DESERIALIZE:
        assert mapper.convert({"int": 42}, th) == 42
    else:
        assert mapper.convert(42, th) == {"int": 42}


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_union_converter_flat_plain_types_not_supported(direction):
    mapper = make_mapper([UnionConverter(direction), PlainDatatypeConverter(direction)])

    th = te.Annotated[t.Union[int, str], Union({"int": int, "str": str}, style=Union.FLAT)]
    if direction == Direction.DESERIALIZE:
        with pytest.raises(ConversionError) as excinfo:
            assert mapper.convert({"type": "int", "int": 42}, th)
        assert "unable to deserialize dict -> int" in str(excinfo.value)
    else:
        with pytest.raises(ConversionError) as excinfo:
            assert mapper.convert(42, th)
        assert "The Union.FLAT style is not supported for plain member types" in str(excinfo.value)


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_schema_converter(direction):
    mapper = make_mapper([SchemaConverter(direction), PlainDatatypeConverter(direction)])

    class Dict1(te.TypedDict):
        a: te.Annotated[int, Alias("afoo", "abar")] = 42
        b: str

    @dataclasses.dataclass
    @typeapi.scoped  # Need this because we're defining the class with a forward reference in a function
    class Class2:
        a: te.Annotated["Dict1", Flattened()]  # The field "a" can be shadowed by a field of its own members
        c: int

    class Dict3(te.TypedDict):
        d: te.Annotated[Class2, Flattened()]

    @dataclasses.dataclass
    class Class4:
        f: te.Annotated[Dict3, Flattened()]

    obj = Class4(Dict3(d=Class2(Dict1(a=42, b="Universe"), c=99)))
    serialized = {"afoo": 42, "b": "Universe", "c": 99}

    if direction == Direction.SERIALIZE:
        assert mapper.convert(obj, Class4) == serialized

        # Test with serializing defaults disabled.
        assert mapper.convert(obj, Class4, settings=[SerializeDefaults(False)]) == {"b": "Universe", "c": 99}

    elif direction == Direction.DESERIALIZE:
        assert mapper.convert(serialized, Class4) == obj

        # Test an extra key.
        serialized = {"abar": 42, "b": "Universe", "c": 99, "d": 42}
        with pytest.raises(ConversionError) as excinfo:
            mapper.convert(serialized, Class4)
        assert str(excinfo.value).splitlines()[0] == "encountered extra keys: {'d'}"

        # Test with extra key, but allowed.
        mapper.convert(serialized, Class4, settings=[ExtraKeys(True)])

        # Test a missing key.
        serialized = {"a": 42, "b": "Universe"}
        with pytest.raises(ConversionError) as excinfo:
            mapper.convert(serialized, Class4)
        assert str(excinfo.value).splitlines()[0] == "missing required field: 'c'"


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_schema_converter_with_dict_member(direction):
    mapper = make_mapper([SchemaConverter(direction), MappingConverter(direction), PlainDatatypeConverter(direction)])

    @dataclasses.dataclass
    class A:
        a: int
        b: t.Dict[str, int]

    if direction == Direction.SERIALIZE:
        assert mapper.convert(A(1, {"spam": 2}), A) == {"a": 1, "b": {"spam": 2}}
    else:
        assert mapper.convert({"a": 1, "b": {"spam": 2}}, A) == A(1, {"spam": 2})


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_schema_converter_remainder_field(direction):
    mapper = make_mapper([SchemaConverter(direction), MappingConverter(direction), PlainDatatypeConverter(direction)])

    @dataclasses.dataclass
    class A:
        a: int
        b: te.Annotated[t.Dict[str, int], Remainder()]

    if direction == Direction.SERIALIZE:
        assert mapper.convert(A(1, {"spam": 2}), A) == {"a": 1, "spam": 2}
    else:
        assert mapper.convert({"a": 1, "spam": 2}, A) == A(1, {"spam": 2})
