import dataclasses
import datetime
import decimal
import enum
import typing as t
import uuid

import pytest
import typing_extensions as te
from databind.core.context import Context, Direction
from databind.core.converter import ConversionError, Converter, NoMatchingConverter
from databind.core.mapper import ObjectMapper
from databind.core.settings import (  # noqa: F401
    Alias,
    DeserializeAs,
    ExtraKeys,
    Flattened,
    Remainder,
    SerializeDefaults,
    Strict,
    Union,
)
from nr.date import duration

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
from databind.json.settings import JsonConverter


def make_mapper(converters: t.List[Converter]) -> ObjectMapper[t.Any, t.Any]:
    mapper = ObjectMapper[t.Any, t.Any]()
    for converter in converters:
        mapper.module.register(converter)
    return mapper


def test_any_converter() -> None:
    mapper = make_mapper([AnyConverter()])
    assert mapper.convert(Direction.SERIALIZE, "foobar", t.Any) == "foobar"
    assert mapper.convert(Direction.SERIALIZE, 42, t.Any) == 42
    assert mapper.convert(Direction.SERIALIZE, t.Any, t.Any) == t.Any


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_plain_datatype_converter(direction: Direction) -> None:
    mapper = make_mapper([PlainDatatypeConverter()])

    # test strict

    assert mapper.convert(direction, "foobar", str) == "foobar"
    assert mapper.convert(direction, 42, int) == 42
    with pytest.raises(ConversionError):
        assert mapper.convert(direction, "42", int)

    # test non-strict

    mapper.settings.add_global(Strict(False))
    if direction == Direction.SERIALIZE:
        with pytest.raises(ConversionError):
            assert mapper.convert(direction, "42", int)

    else:
        assert mapper.convert(direction, "42", int) == 42
        with pytest.raises(ConversionError):
            mapper.convert(direction, "foobar", int)


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_decimal_converter(direction: Direction) -> None:
    mapper = make_mapper([DecimalConverter()])

    pi = decimal.Decimal("3.141592653589793")
    if direction == Direction.SERIALIZE:
        assert mapper.convert(direction, pi, decimal.Decimal) == str(pi)

    else:
        assert mapper.convert(direction, str(pi), decimal.Decimal) == pi
        with pytest.raises(ConversionError):
            assert mapper.convert(direction, 3.14, decimal.Decimal)
        assert mapper.convert(direction, 3.14, decimal.Decimal, settings=[Strict(False)]) == decimal.Decimal(3.14)


@pytest.mark.parametrize("direction", (Direction.DESERIALIZE, Direction.SERIALIZE))
# @pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_enum_converter(direction: Direction) -> None:
    mapper = make_mapper([EnumConverter()])

    class Pet(enum.Enum):
        CAT = enum.auto()
        DOG = enum.auto()
        LION: te.Annotated[int, Alias("KITTY")] = enum.auto()

    if direction == Direction.SERIALIZE:
        assert mapper.convert(direction, Pet.CAT, Pet) == "CAT"
        assert mapper.convert(direction, Pet.DOG, Pet) == "DOG"
        assert mapper.convert(direction, Pet.LION, Pet) == "KITTY"
    else:
        assert mapper.convert(direction, "CAT", Pet) == Pet.CAT
        assert mapper.convert(direction, "DOG", Pet) == Pet.DOG
        assert mapper.convert(direction, "KITTY", Pet) == Pet.LION

    class Flags(enum.IntEnum):
        A = 1
        B = 2

    if direction == Direction.SERIALIZE:
        assert mapper.convert(direction, Flags.A, Flags) == 1
        assert mapper.convert(direction, Flags.B, Flags) == 2
        with pytest.raises(ConversionError):
            assert mapper.convert(direction, Flags.A | Flags.B, Flags)
    else:
        assert mapper.convert(direction, 1, Flags) == Flags.A
        assert mapper.convert(direction, 2, Flags) == Flags.B
        with pytest.raises(ConversionError):
            assert mapper.convert(direction, 3, Flags)


def test_optional_converter() -> None:
    mapper = make_mapper([OptionalConverter(), PlainDatatypeConverter()])
    assert mapper.convert(Direction.SERIALIZE, 42, t.Optional[int]) == 42
    assert mapper.convert(Direction.SERIALIZE, None, t.Optional[int]) is None
    assert mapper.convert(Direction.SERIALIZE, 42, int) == 42
    with pytest.raises(ConversionError):
        assert mapper.convert(Direction.SERIALIZE, None, int)


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_datetime_converter(direction: Direction) -> None:
    mapper = make_mapper([DatetimeConverter()])

    tests = [
        (datetime.time(11, 30, 10), "11:30:10.0"),
        (datetime.date(2022, 2, 4), "2022-02-04"),
        (datetime.datetime(2022, 2, 4, 11, 30, 10), "2022-02-04T11:30:10.0"),
    ]

    for py_value, str_value in tests:
        if direction == Direction.SERIALIZE:
            assert mapper.convert(direction, py_value, type(py_value)) == str_value
        else:
            assert mapper.convert(direction, str_value, type(py_value)) == py_value


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_duration_converter(direction: Direction) -> None:
    mapper = make_mapper([StringifyConverter(duration, duration.parse), SchemaConverter(), PlainDatatypeConverter()])

    # Test parsing duration from strings.

    test_from_strings = [
        (duration(2, 1, 4, 0, 3), "P2Y1M4WT3H"),
        (duration(seconds=10), "PT10S"),
        (duration(days=1, minutes=5), "P1DT5M"),
    ]

    for py_value, str_value in test_from_strings:
        if direction == Direction.SERIALIZE:
            assert mapper.convert(direction, py_value, duration) == str_value
        else:
            assert mapper.convert(direction, str_value, duration) == py_value

    # Test parsing duration from objects (it is also a dataclass).

    test_from_dicts = [
        (duration(2, 1, 4, 0, 3), {"years": 2, "months": 1, "weeks": 4, "hours": 3}),
        (duration(seconds=10), {"seconds": 10}),
        (duration(days=1, minutes=5), {"days": 1, "minutes": 5}),
    ]

    for py_value, obj_value in test_from_dicts:
        if direction == Direction.SERIALIZE:
            assert mapper.convert(direction, py_value, duration) == str(py_value)  # obj_value
        else:
            assert mapper.convert(direction, obj_value, duration) == py_value


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_stringify_converter(direction: Direction) -> None:
    mapper = make_mapper([StringifyConverter(uuid.UUID)])

    uid = uuid.uuid4()
    if direction == Direction.SERIALIZE:
        assert mapper.convert(direction, uid, uuid.UUID) == str(uid)
    else:
        assert mapper.convert(direction, str(uid), uuid.UUID) == uid


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_mapping_converter(direction: Direction) -> None:
    mapper = make_mapper([AnyConverter(), MappingConverter(), PlainDatatypeConverter()])
    assert mapper.convert(direction, {"a": 1}, t.Mapping) == {"a": 1}
    assert mapper.convert(direction, {"a": 1}, t.Mapping[str, int]) == {"a": 1}
    assert mapper.convert(direction, {"a": 1}, t.MutableMapping[str, int]) == {"a": 1}
    assert mapper.convert(direction, {"a": 1}, t.Dict[str, int]) == {"a": 1}
    with pytest.raises(ConversionError):
        assert mapper.convert(direction, 1, t.Mapping[int, str])

    K = t.TypeVar("K")
    V = t.TypeVar("V")

    class CustomDict(t.Dict[K, V]):
        pass

    if direction == Direction.SERIALIZE:
        assert mapper.convert(direction, CustomDict({"a": 1}), CustomDict[str, int]) == {"a": 1}
    else:
        assert mapper.convert(direction, {"a": 1}, CustomDict[str, int]) == CustomDict({"a": 1})

    # class FixedDict(t.Dict[int, str]):
    #   pass
    # if direction == Direction.SERIALIZE:
    #   assert mapper.convert(direction, FixedDict({"a": 1}), FixedDict) == {"a": 1}
    # else:
    #   assert mapper.convert(direction, {"a": 1}, FixedDict) == FixedDict({"a": 1})


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_collection_converter(direction: Direction) -> None:
    mapper = make_mapper([AnyConverter(), CollectionConverter(), PlainDatatypeConverter()])
    assert mapper.convert(direction, [1, 2, 3], t.Collection) == [1, 2, 3]
    assert mapper.convert(direction, [1, 2, 3], t.Collection[int]) == [1, 2, 3]
    assert mapper.convert(direction, [1, 2, 3], t.MutableSequence[int]) == [1, 2, 3]
    assert mapper.convert(direction, [1, 2, 3], t.List[int]) == [1, 2, 3]
    with pytest.raises(ConversionError):
        assert mapper.convert(direction, 1, t.Mapping[int, str])

    T = t.TypeVar("T")

    class CustomList(t.List[T]):
        pass

    if direction == Direction.SERIALIZE:
        assert mapper.convert(direction, CustomList([1, 2, 3]), CustomList[int]) == [1, 2, 3]
    else:
        assert mapper.convert(direction, [1, 2, 3], CustomList[int]) == CustomList([1, 2, 3])

    # class FixedList(t.List[int]):
    #   pass
    # if direction == Direction.SERIALIZE:
    #   assert mapper.convert(direction, FixedList([1, 2, 3]), FixedList) == [1, 2, 3]
    # else:
    #   assert mapper.convert(direction, [1, 2, 3], FixedList) == FixedList([1, 2, 3])


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_union_converter_nested(direction: Direction) -> None:
    mapper = make_mapper([UnionConverter(), PlainDatatypeConverter()])

    hint = te.Annotated[t.Union[int, str], Union({"int": int, "str": str})]
    if direction == Direction.DESERIALIZE:
        assert mapper.convert(direction, {"type": "int", "int": 42}, hint) == 42
    else:
        assert mapper.convert(direction, 42, hint) == {"type": "int", "int": 42}


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_union_converter_best_match(direction: Direction) -> None:
    mapper = make_mapper([UnionConverter(), PlainDatatypeConverter()])

    if direction == Direction.DESERIALIZE:
        assert mapper.convert(direction, 42, t.Union[int, str]) == 42
    else:
        assert mapper.convert(direction, 42, t.Union[int, str]) == 42


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_union_converter_keyed(direction: Direction) -> None:
    mapper = make_mapper([UnionConverter(), PlainDatatypeConverter()])

    th = te.Annotated[t.Union[int, str], Union({"int": int, "str": str}, style=Union.KEYED)]
    if direction == Direction.DESERIALIZE:
        assert mapper.convert(direction, {"int": 42}, th) == 42
    else:
        assert mapper.convert(direction, 42, th) == {"int": 42}


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_union_converter_flat_plain_types_not_supported(direction: Direction) -> None:
    mapper = make_mapper([UnionConverter(), PlainDatatypeConverter()])

    th = te.Annotated[t.Union[int, str], Union({"int": int, "str": str}, style=Union.FLAT)]
    if direction == Direction.DESERIALIZE:
        with pytest.raises(ConversionError) as excinfo:
            assert mapper.convert(direction, {"type": "int", "int": 42}, th)
        assert "unable to deserialize dict -> int" in str(excinfo.value)
    else:
        with pytest.raises(ConversionError) as excinfo:
            assert mapper.convert(direction, 42, th)
        assert "The Union.FLAT style is not supported for plain member types" in str(excinfo.value)


# TODO(NiklasRosenstein): Bring back dataclass definitions in function bodies.

# @pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
# def test_schema_converter(direction: Direction):
#     mapper = make_mapper([SchemaConverter(), PlainDatatypeConverter()])

#     class Dict1(te.TypedDict):
#         a: te.Annotated[int, Alias("afoo", "abar")] = 42
#         b: str

#     @dataclasses.dataclass
#     @typeapi.scoped  # Need this because we're defining the class with a forward reference in a function
#     class Class2:
#         a: te.Annotated["Dict1", Flattened()]  # The field "a" can be shadowed by a field of its own members
#         c: int

#     class Dict3(te.TypedDict):
#         d: te.Annotated[Class2, Flattened()]

#     @dataclasses.dataclass
#     class Class4:
#         f: te.Annotated[Dict3, Flattened()]

#     obj = Class4(Dict3(d=Class2(Dict1(a=42, b="Universe"), c=99)))
#     serialized = {"afoo": 42, "b": "Universe", "c": 99}

#     if direction == Direction.SERIALIZE:
#         assert mapper.convert(direction, obj, Class4) == serialized

#         # Test with serializing defaults disabled.
#         assert mapper.convert(direction, obj, Class4, settings=[SerializeDefaults(False)]) == {"b": "Universe", "c": 99}  # noqa: E501

#     elif direction == Direction.DESERIALIZE:
#         assert mapper.convert(direction, serialized, Class4) == obj

#         # Test an extra key.
#         serialized = {"abar": 42, "b": "Universe", "c": 99, "d": 42}
#         with pytest.raises(ConversionError) as excinfo:
#             mapper.convert(direction, serialized, Class4)
#         assert str(excinfo.value).splitlines()[0] == "encountered extra keys: {'d'}"

#         # Test with extra key, but allowed.
#         mapper.convert(direction, serialized, Class4, settings=[ExtraKeys()])

#         # Test a missing key.
#         serialized = {"a": 42, "b": "Universe"}
#         with pytest.raises(ConversionError) as excinfo:
#             mapper.convert(direction, serialized, Class4)
#         assert str(excinfo.value).splitlines()[0] == "missing required field: 'c'"


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_schema_converter_with_dict_member(direction: Direction) -> None:
    mapper = make_mapper([SchemaConverter(), MappingConverter(), PlainDatatypeConverter()])

    @dataclasses.dataclass
    class A:
        a: int
        b: t.Dict[str, int]

    if direction == Direction.SERIALIZE:
        assert mapper.convert(direction, A(1, {"spam": 2}), A) == {"a": 1, "b": {"spam": 2}}
    else:
        assert mapper.convert(direction, {"a": 1, "b": {"spam": 2}}, A) == A(1, {"spam": 2})


@pytest.mark.parametrize("direction", (Direction.SERIALIZE, Direction.DESERIALIZE))
def test_schema_converter_remainder_field(direction: Direction) -> None:
    mapper = make_mapper([SchemaConverter(), MappingConverter(), PlainDatatypeConverter()])

    @dataclasses.dataclass
    class A:
        a: int
        b: te.Annotated[t.Dict[str, int], Remainder()]

    if direction == Direction.SERIALIZE:
        assert mapper.serialize(A(1, {"spam": 2}), A) == {"a": 1, "spam": 2}
    else:
        assert mapper.deserialize({"a": 1, "spam": 2}, A) == A(1, {"spam": 2})


def test_deserialize_as() -> None:
    mapper = make_mapper([SchemaConverter(), PlainDatatypeConverter()])

    @dataclasses.dataclass
    class A:
        a: int

    @dataclasses.dataclass
    class B(A):
        a: int = 42

    @dataclasses.dataclass
    class MyClass:
        a: te.Annotated[A, DeserializeAs(B)]

    with pytest.raises(ConversionError) as excinfo:
        assert mapper.serialize(MyClass(A(1)), MyClass) == {"a": {"a": 1}}
    assert (
        str(excinfo.value)
        == f"""expected converters_test.test_deserialize_as.<locals>.B, got converters_test.test_deserialize_as.\
<locals>.A instead

Trace:
    $: TypeHint(converters_test.test_deserialize_as.<locals>.MyClass)
    .a: TypeHint({te.Annotated[A, DeserializeAs(B)]})"""
    )

    assert mapper.serialize(MyClass(B(2)), MyClass) == {"a": {"a": 2}}
    assert mapper.deserialize({"a": {"a": 1}}, MyClass) == MyClass(B(1))
    assert mapper.deserialize({"a": {"a": 2}}, MyClass) == MyClass(B(2))
    assert mapper.deserialize({"a": {}}, MyClass) == MyClass(B(42))


def test_deserialize_union_dataclass_subclass() -> None:
    """Tests that a subclass of a dataclass marked as a union is deserialized as a dataclass."""

    @dataclasses.dataclass
    @Union(style=Union.FLAT)
    class A:
        id: int

    @Union.register(A)
    @dataclasses.dataclass
    class B(A):
        name: str

    from databind.json import load

    assert load({"type": "B", "id": 0, "name": "spam"}, A) == B(0, "spam")
    assert load({"id": 0, "name": "spam"}, B) == B(0, "spam")


def test_deserialize_and_serialize_literal_union() -> None:
    from databind.json import dump, load

    @dataclasses.dataclass
    class AwsMachine:
        region: str
        name: str
        instance_id: str
        provider: te.Literal["aws"] = "aws"

    @dataclasses.dataclass
    class AzureMachine:
        resource_group: str
        name: str
        provider: te.Literal["azure"] = "azure"

    Machine = t.Union[AwsMachine, AzureMachine]

    aws_payload = {"provider": "aws", "region": "eu-central-1", "name": "bar", "instance_id": "42"}
    aws_machine = AwsMachine("eu-central-1", "bar", "42")
    assert load(aws_payload, Machine) == aws_machine
    assert dump(aws_machine, Machine) == aws_payload
    assert dump(aws_machine, AwsMachine) == aws_payload

    azure_payload = {"provider": "azure", "resource_group": "foo", "name": "bar"}
    azure_machine = AzureMachine("foo", "bar")
    assert load(azure_payload, Machine) == azure_machine
    assert dump(azure_machine, Machine) == azure_payload
    assert dump(azure_machine, AzureMachine) == azure_payload


def test_json_converter_setting() -> None:
    from databind.json import dump, load

    class MyConverter(Converter):
        def __init__(self, return_value: t.Any, skip: bool = False) -> None:
            self.return_value = return_value
            self.skip = skip
            super().__init__()

        def convert(self, ctx: Context) -> t.Any:
            if self.skip:
                raise NotImplementedError
            return self.return_value

    @JsonConverter(MyConverter("Oh HELLO"))
    @dataclasses.dataclass
    class MyClass1:
        a: int

    assert load({"a": 42}, MyClass1) == "Oh HELLO"  # type: ignore[comparison-overlap]  # Non-overlapping equality check  # noqa: E501
    assert load({}, MyClass1) == "Oh HELLO"  # type: ignore[comparison-overlap]  # Non-overlapping equality check  # noqa: E501
    assert load({}, te.Annotated[MyClass1, JsonConverter(MyConverter("I am better"))]) == "I am better"

    class AnotherClass:
        ...

    with pytest.raises(NoMatchingConverter):
        assert dump(None, AnotherClass)

    assert dump(None, te.Annotated[AnotherClass, JsonConverter(MyConverter(42))]) == 42

    @dataclasses.dataclass
    class MyClass2:
        a: int

    assert load({"a": 42}, MyClass1) == "Oh HELLO"  # type: ignore[comparison-overlap]  # Non-overlapping equality check  # noqa: E501
    assert load({"a": 42}, MyClass2) == MyClass2(42)
    assert load({"a": 42}, te.Annotated[MyClass2, JsonConverter(MyConverter("foo"))]) == "foo"
    assert load({"a": 42}, te.Annotated[MyClass2, JsonConverter(MyConverter(None, skip=True))]) == MyClass2(42)


def test_deserialize_tuple() -> None:
    import databind.json

    assert databind.json.load([1, 2], t.Tuple[int, int]) == (1, 2)
    assert databind.json.load([1, "foo"], t.Tuple[int, str]) == (1, "foo")
    assert databind.json.load([1, 2, 3], t.Tuple[int, ...]) == (1, 2, 3)
    assert databind.json.load([], t.Tuple[int, ...]) == ()

    with pytest.raises(ConversionError) as excinfo:
        databind.json.load([1, 42], t.Tuple[int, str])
    assert excinfo.value.message == "unable to deserialize int -> str"

    with pytest.raises(ConversionError) as excinfo:
        databind.json.load([1, 42, 3], t.Tuple[int, int])
    assert excinfo.value.message == "expected a tuple of length 2, found 3"
