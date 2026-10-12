from __future__ import annotations

import dis
import json
import random
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import FrameType

import pytest
from aware_meta_type_schema import encoding
from aware_meta_type_schema.encoding import (
    FrozenJson,
    JsonValue,
    TypeSchemaEncodingError,
    _canonical_json_native_for_origin,
    canonical_json,
    normalize_json,
)

LITERALS = (
    ("{}", {}),
    ("[]", []),
    ("null", None),
    ("true", True),
    ("false", False),
    ("0", 0),
)


@pytest.mark.parametrize(("text", "expected"), LITERALS)
def test_exact_literals_match_unchanged_oracle(text: str, expected: JsonValue) -> None:
    frozen = FrozenJson(text)
    result = frozen.to_wire()
    oracle = normalize_json(json.loads(text))
    assert result == oracle == expected
    assert type(result) is type(oracle) is type(expected)
    assert frozen.canonical == canonical_json(result) == text


@pytest.mark.parametrize(("text", "expected"), LITERALS)
def test_only_exact_literals_skip_parser_and_normalizer(
    text: str, expected: JsonValue, monkeypatch: pytest.MonkeyPatch
) -> None:
    frozen = FrozenJson(text)

    def forbidden(*_args: object, **_kwargs: object) -> object:
        pytest.fail("exact literal unexpectedly used the fallback")

    monkeypatch.setattr(json, "loads", forbidden)
    monkeypatch.setattr(encoding, "normalize_json", forbidden)
    assert frozen.to_wire() == expected


@pytest.mark.parametrize("text", ["{}", "[]"])
def test_empty_containers_are_fresh_and_isolated(text: str) -> None:
    first, second = FrozenJson(text), FrozenJson(text)
    result = first.to_wire()
    assert result is not first.to_wire()
    assert result is not second.to_wire()
    if isinstance(result, dict):
        result["caller"] = ["mutable"]
    else:
        assert isinstance(result, list)
        result.append({"caller": True})
    assert first.to_wire() == second.to_wire() == normalize_json(json.loads(text))
    assert first.canonical == second.canonical == text


@pytest.mark.parametrize(
    "text", ['""', '"雪\\n"', "1", "-1", "[0,{},[]]", '{"x":true}']
)
def test_other_values_keep_parser_and_normalizer(
    text: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    frozen = FrozenJson(text)
    calls: list[str] = []
    normalized: list[object] = []
    original_loads = json.loads

    def loads(current: str) -> object:
        calls.append(current)
        return original_loads(current)

    def normalize(value: object, *, path: str = "$") -> JsonValue:
        normalized.append(value)
        return normalize_json(value, path=path)

    monkeypatch.setattr(json, "loads", loads)
    monkeypatch.setattr(encoding, "normalize_json", normalize)
    result = frozen.to_wire()
    assert calls == [text]
    assert normalized
    assert result == normalize_json(original_loads(text))


class MisleadingString(str):
    def __eq__(self, other: object) -> bool:
        return True

    __hash__ = str.__hash__


class ExplosiveString(str):
    def __eq__(self, other: object) -> bool:
        raise AssertionError("string subclass equality must not select a fast path")

    __hash__ = str.__hash__


@pytest.mark.parametrize("string_type", [str, MisleadingString, ExplosiveString])
@pytest.mark.parametrize("text", [pair[0] for pair in LITERALS] + ['{"nested":[1]}'])
def test_string_subclasses_use_exact_original_fallback(
    string_type: type[str], text: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    frozen = FrozenJson("null")
    current = string_type(text)
    object.__setattr__(frozen, "canonical", current)
    calls: list[object] = []
    original_loads = json.loads

    def loads(value: str) -> object:
        calls.append(value)
        return original_loads(value)

    monkeypatch.setattr(json, "loads", loads)
    assert frozen.to_wire() == normalize_json(original_loads(current))
    assert len(calls) == (0 if string_type is str and text in dict(LITERALS) else 1)
    if calls:
        assert calls[0] is current


def test_each_call_reads_current_string_without_cached_value() -> None:
    frozen = FrozenJson("{}")
    previous = frozen.to_wire()
    for text in [pair[0] for pair in LITERALS] + ['{"x":[1]}', '"changed"', "42"]:
        object.__setattr__(frozen, "canonical", text)
        assert frozen.to_wire() == normalize_json(json.loads(text))
    assert previous == {}
    object.__setattr__(frozen, "canonical", "not JSON")
    with pytest.raises(json.JSONDecodeError):
        frozen.to_wire()


def outcome(call: Callable[[], object]) -> tuple[object, object]:
    try:
        result = call()
    except (TypeError, ValueError) as error:
        return type(error), str(error)
    return type(result), result


@pytest.mark.parametrize(
    "current",
    [
        "",
        " ",
        "{",
        "[1,]",
        "not JSON",
        "0.0",
        "-0.0",
        "NaN",
        "Infinity",
        '{"":0}',
        '{"x":[0.1]}',
        " {} ",
        "-0",
        "0\n",
        None,
        0,
        True,
        [],
        b"{}",
        bytearray(b"[]"),
        object(),
        MisleadingString("not JSON"),
        ExplosiveString("0.0"),
    ],
)
def test_replaced_malformed_or_noncanonical_values_preserve_oracle(
    current: object,
) -> None:
    frozen = FrozenJson("null")
    object.__setattr__(frozen, "canonical", current)

    def oracle() -> JsonValue:
        # Deliberately pass malformed types exactly as the old implementation did.
        return normalize_json(json.loads(current))  # type: ignore[arg-type]

    assert outcome(frozen.to_wire) == outcome(oracle)


@pytest.mark.parametrize("text", [" {} ", "0\n", "-0", '{"b":1,"a":0}'])
def test_constructor_canonicality_is_unchanged(text: str) -> None:
    with pytest.raises(TypeSchemaEncodingError, match="must be canonical"):
        FrozenJson(text)


def test_constructor_and_factory_errors_are_unchanged() -> None:
    with pytest.raises(TypeError, match="canonical must be str"):
        FrozenJson(None)  # type: ignore[arg-type]
    with pytest.raises(TypeSchemaEncodingError, match="invalid JSON"):
        FrozenJson("not JSON")
    with pytest.raises(TypeSchemaEncodingError, match="uses float"):
        FrozenJson.from_value({"x": 0.5})
    with pytest.raises(TypeSchemaEncodingError, match="keys must be non-empty"):
        FrozenJson.from_value({"": 0})


def test_deterministic_nested_corpus_is_canonically_equivalent_and_isolated() -> None:
    random_source = random.Random(279280)
    scalars: list[JsonValue] = [None, False, True, 0, -1, 1, 10**100, "", "雪", '"\\\n']

    def value(depth: int) -> JsonValue:
        if not depth or random_source.randrange(3) == 0:
            return random_source.choice(scalars)
        children = [value(depth - 1) for _ in range(random_source.randrange(6))]
        if random_source.randrange(2):
            return children
        return {f"key:{index}": child for index, child in enumerate(children)}

    corpus = scalars + [{"wide": list(range(200))}, {"nested": [[[[None]]]]}]
    corpus.extend(value(5) for _ in range(1000))
    for original in corpus:
        text = canonical_json(original)
        assert _canonical_json_native_for_origin(original) == text
        frozen = FrozenJson(text)
        result = frozen.to_wire()
        assert outcome(frozen.to_wire) == outcome(
            lambda current=text: normalize_json(json.loads(current))
        )
        assert canonical_json(result) == text
        if isinstance(result, dict):
            result["caller-added"] = True
        elif isinstance(result, list):
            result.append("caller-added")
        assert canonical_json(frozen.to_wire()) == text
        assert frozen.canonical == text


def test_origin_native_backend_has_no_live_global_dispatch() -> None:
    # This private prerequisite has no Python recursive/stdlib call boundary.
    # A future Origin entrance must separately protect its retained closure.
    assert not any(
        instruction.opname == "LOAD_GLOBAL"
        for instruction in dis.get_instructions(_canonical_json_native_for_origin)
    )


@pytest.mark.parametrize("member", ["__init__", "encode", "iterencode", "default"])
def test_origin_native_backend_eliminates_python_encoder_dispatch(
    member: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    entered: list[str] = []
    original_constructor = json.JSONEncoder.__init__.__code__

    def foreign(*_args: object, **_kwargs: object) -> object:
        calls.append(member)
        return "{}"

    def observe(frame: FrameType, event: str, _arg: object):
        if event == "return" and frame.f_code is original_constructor:
            entered.append("JSONEncoder.__init__")
        return observe

    expected = canonical_json({"n": 1, "nested": [None, "雪", True]})
    monkeypatch.setattr(json.JSONEncoder, member, foreign)
    previous_trace = sys.gettrace()
    try:
        sys.settrace(observe)
        result = _canonical_json_native_for_origin(
            {"n": 1, "nested": [None, "雪", True]}
        )
    finally:
        sys.settrace(previous_trace)
    assert result == expected
    assert calls == []
    # The previously vulnerable constructor-return path is absent, rather than
    # an injection point claimed to have been reached in this implementation.
    assert entered == []


@pytest.mark.parametrize("member", ["__new__", "__init__", "__call__"])
@pytest.mark.parametrize("poison", ["callable", "descriptor"])
def test_origin_native_backend_retains_descriptors_not_just_heap_type(
    member: str,
    poison: str,
) -> None:
    # Mutating __new__ changes CPython type slots even if an attribute setter
    # subsequently restores its visible descriptor. Isolate every type poison.
    source = """
import _json
import sys
from aware_meta_type_schema.encoding import (
    TypeSchemaEncodingError, _canonical_json_native_for_origin,
)
calls = []
def foreign(*args, **kwargs):
    calls.append('FOREIGN')
    return None
class ForeignDescriptor:
    def __get__(self, instance, owner=None):
        calls.append('FOREIGN_DESCRIPTOR_GET')
        raise RuntimeError('foreign descriptor getter executed')
replacement = foreign if sys.argv[2] == 'callable' else ForeignDescriptor()
setattr(_json.make_encoder, sys.argv[1], replacement)
raw_namespace = type.__dict__['__dict__'].__get__(_json.make_encoder)
assert raw_namespace[sys.argv[1]] is replacement
try:
    _canonical_json_native_for_origin({'n': [1, False]})
except ValueError as error:
    assert type(error) is ValueError
    assert error.args == ('origin_native_backend_changed',)
else:
    raise AssertionError('backend substitution not refused')
assert calls == []
print('REFUSED')
"""
    root = str(Path(encoding.__file__).resolve().parents[1])
    result = subprocess.run(
        [sys.executable, "-B", "-c", source, member, poison],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "REFUSED\n"
    assert result.stderr == ""


@pytest.mark.parametrize("target", ["encoder", "quote", "normalize", "set", "type"])
def test_origin_native_backend_retains_capabilities_during_invocation(
    target: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    injected: list[str] = []
    code = _canonical_json_native_for_origin.__code__
    expected = canonical_json({"n": 1})

    def foreign(*_args: object, **_kwargs: object) -> object:
        calls.append(target)
        return None

    def observe(frame: FrameType, event: str, _arg: object):
        # Observe genuine execution, after the native capabilities have been
        # copied into invocation locals and before encoder creation.
        if (
            event == "line"
            and frame.f_code is code
            and "root" in frame.f_locals
            and not injected
        ):
            injected.append(target)
            if target == "encoder":
                monkeypatch.setattr(json.encoder, "c_make_encoder", foreign)
            elif target == "quote":
                monkeypatch.setattr(json.encoder, "encode_basestring", foreign)
            elif target == "normalize":
                monkeypatch.setattr(encoding, "normalize_json", foreign)
            else:
                monkeypatch.setattr(encoding, target, foreign, raising=False)
        return observe

    previous_trace = sys.gettrace()
    try:
        sys.settrace(observe)
        result = _canonical_json_native_for_origin({"n": 1})
    finally:
        sys.settrace(previous_trace)
    assert injected == [target]
    assert calls == []
    assert result == expected


@pytest.mark.parametrize("location", ["root", "list", "dictionary", "key"])
def test_origin_native_backend_refuses_foreign_values_before_behavior(
    location: str,
) -> None:
    calls: list[str] = []

    class ForeignMeta(type):
        def __eq__(cls, other: object) -> bool:
            calls.append("metaclass equality")
            return False

    class Foreign(metaclass=ForeignMeta):
        def __getattribute__(self, name: str) -> object:
            calls.append("attribute")
            return object.__getattribute__(self, name)

        def __eq__(self, other: object) -> bool:
            calls.append("equality")
            return False

        __hash__ = object.__hash__

    foreign = Foreign()
    values = {
        "root": foreign,
        "list": [foreign],
        "dictionary": {"nested": foreign},
        "key": {foreign: 1},
    }
    with pytest.raises(ValueError, match="origin_native_data_invalid"):
        _canonical_json_native_for_origin(values[location])
    assert calls == []


@pytest.mark.parametrize("base", [str, int, list, dict])
def test_origin_native_backend_refuses_native_subclasses_without_dispatch(
    base: type,
) -> None:
    calls: list[str] = []

    class Foreign(base):
        def __iter__(self):
            calls.append("iteration")
            return iter(())

        def __eq__(self, other: object) -> bool:
            calls.append("equality")
            return False

    value = Foreign()
    with pytest.raises(ValueError, match="origin_native_data_invalid"):
        _canonical_json_native_for_origin({"nested": value})
    assert calls == []


@pytest.mark.parametrize("member", ["__new__", "__init__"])
def test_origin_native_backend_refusal_bypasses_error_constructor(
    member: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def foreign(*_args: object, **_kwargs: object) -> object:
        calls.append(member)
        return None

    monkeypatch.setattr(TypeSchemaEncodingError, member, foreign, raising=False)
    with pytest.raises(ValueError, match="origin_native_data_invalid"):
        _canonical_json_native_for_origin({"nested": 0.5})
    assert calls == []


def test_origin_native_backend_cycles_limits_and_shared_values() -> None:
    cycle: list[object] = []
    cycle.append(cycle)
    with pytest.raises(ValueError, match="origin_native_data_limit"):
        _canonical_json_native_for_origin(cycle)
    nested: object = []
    for _ in range(64):
        nested = [nested]
    with pytest.raises(ValueError, match="origin_native_data_limit"):
        _canonical_json_native_for_origin(nested)
    shared: list[object] = [1, {"雪": True}]
    value = {"one": shared, "two": shared}
    assert _canonical_json_native_for_origin(value) == canonical_json(value)
    assert value["one"] is value["two"] is shared
