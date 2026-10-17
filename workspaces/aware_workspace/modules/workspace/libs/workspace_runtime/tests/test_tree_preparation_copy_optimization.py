"""Fresh preparation metadata, original copying semantics and genuine custody."""

from __future__ import annotations

import dataclasses
import json
from collections import defaultdict, namedtuple

import pytest
from aware_file_system.confined_mutation import (
    ConfinedTreeEntryPin,
    ConfinedTreePreparationObservation,
    ConfinedTreeScratchEffect,
)
from aware_workspace_runtime.repository_tree_preparation_copy import (
    copy_preparation_observation,
)
from test_repository_tree_projection import setup
from test_repository_workflow import (
    inputs as inputs,  # noqa: PLC0414 -- original fixture
)


def _observation(*, count=3):
    return ConfinedTreePreparationObservation(
        "preparation:copy",
        "request:copy",
        "sha256:" + "a" * 64,
        (1, 2),
        tuple((i, f"file-{i:04}.txt", "CREATE") for i in range(count)),
        tuple((f"file-{i:04}.txt", ConfinedTreeEntryPin(False)) for i in range(count)),
        tuple(
            ConfinedTreeScratchEffect(
                f".scratch-{i}", "temporary_file", i, "create", 0o600
            )
            for i in range(count)
        ),
        8192,
    )


@pytest.mark.parametrize("count", [0, 1, 1000])
def test_fresh_complete_copy_preserves_exact_payload_and_canonical_json(count):
    original = _observation(count=count)
    actual = copy_preparation_observation(original)
    expected = dataclasses.asdict(original)
    assert actual == expected and actual is not expected
    assert json.dumps(actual, sort_keys=True, ensure_ascii=False) == json.dumps(
        expected, sort_keys=True, ensure_ascii=False
    )
    if count:
        original_pin = original.read_pins[0][1]
        object.__setattr__(original_pin, "exists", True)
        assert copy_preparation_observation(original) == dataclasses.asdict(original)
        assert actual["read_pins"][0][1]["exists"] is False


@pytest.mark.parametrize("metadata", ["reorder", "rename", "filter", "append"])
def test_current_field_metadata_and_dictionary_order_match_original(metadata):
    cls = ConfinedTreeScratchEffect
    original_fields = cls.__dataclass_fields__
    field = original_fields["role"]
    name, flag = field.name, field._field_type
    row = ConfinedTreeScratchEffect("path", "role", 1, "create", 0o600)
    try:
        if metadata == "reorder":
            cls.__dataclass_fields__ = dict(reversed(tuple(original_fields.items())))
        elif metadata == "rename":
            field.name = "path"
        elif metadata == "filter":
            field._field_type = dataclasses._FIELD_CLASSVAR
        else:
            extra = dataclasses.field(default=None)
            extra.name = "role"
            extra._field_type = dataclasses._FIELD
            cls.__dataclass_fields__ = {**original_fields, "extra": extra}
        expected = dataclasses.asdict(row)
        actual = copy_preparation_observation(row)
        assert actual == expected and tuple(actual) == tuple(expected)
    finally:
        cls.__dataclass_fields__ = original_fields
        field.name, field._field_type = name, flag


@pytest.mark.parametrize("mutation", ["name", "order", "flag"])
def test_deepcopy_callback_preserves_snapshot_and_later_field_reads(mutation):
    cls = ConfinedTreeScratchEffect
    original_fields = cls.__dataclass_fields__
    later = original_fields["role"]
    original_name, original_flag = later.name, later._field_type
    outcomes = []
    calls = []

    class Leaf:
        def __deepcopy__(self, memo):
            calls.append("copy")
            if mutation == "name":
                later.name = "path"
            elif mutation == "order":
                cls.__dataclass_fields__ = dict(
                    reversed(tuple(original_fields.items()))
                )
            else:
                later._field_type = dataclasses._FIELD_CLASSVAR
            return "copied"

    for copier in (dataclasses.asdict, copy_preparation_observation):
        row = ConfinedTreeScratchEffect(Leaf(), "role", 1, "create", 0o600)
        try:
            outcomes.append(copier(row))
        finally:
            cls.__dataclass_fields__ = original_fields
            later.name, later._field_type = original_name, original_flag
    assert outcomes[0] == outcomes[1] and tuple(outcomes[0]) == tuple(outcomes[1])
    assert calls == ["copy"] * (4 if mutation == "name" else 2)


@pytest.mark.parametrize(
    "kind",
    [
        "namedtuple",
        "list",
        "dict",
        "defaultdict",
        "subclass",
        "unicode",
        "float",
        "invalid",
    ],
)
def test_unknown_fields_preserve_generic_copy_and_json_errors(kind):
    class Pin(ConfinedTreeEntryPin):
        pass

    Point = namedtuple("Point", "first second")
    values = {
        "namedtuple": Point(1, ["a"]),
        "list": [1, {"a": 2}],
        "dict": {1: (2, 3)},
        "defaultdict": defaultdict(list, {"key": [1]}),
        "subclass": Pin(False),
        "unicode": "雪",
        "float": float("nan"),
        "invalid": object(),
    }
    row = _observation()
    object.__setattr__(row, "preparation_ref", values[kind])
    actual = copy_preparation_observation(row)
    expected = dataclasses.asdict(row)
    if kind == "invalid":
        assert type(actual["preparation_ref"]) is object
        assert type(expected["preparation_ref"]) is object
    elif kind != "float":
        assert actual == expected
    assert type(actual["preparation_ref"]) is type(expected["preparation_ref"])
    results = []
    for value in (expected, actual):
        try:
            results.append(
                (
                    "return",
                    json.dumps(
                        value, sort_keys=True, ensure_ascii=False, allow_nan=False
                    ),
                )
            )
        except (TypeError, ValueError) as error:
            results.append(("error", type(error), str(error)))
    # object repr addresses occur in TypeError text only as its type name.
    assert results[0] == results[1]


@pytest.mark.parametrize(
    "entry", ["fields", "_asdict_inner", "asdict", "_is_dataclass_instance"]
)
@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
def test_substituted_stdlib_helpers_are_rejected_before_dispatch(entry, behavior):
    original = getattr(dataclasses, entry)
    calls = []

    def foreign(*args, **kwargs):
        calls.append(True)
        if behavior == "restore":
            setattr(dataclasses, entry, original)
        if behavior == "raise":
            raise AssertionError("foreign copy helper executed")
        return {}

    row = _observation()
    setattr(dataclasses, entry, foreign)
    error = None
    try:
        copy_preparation_observation(row)
    except TypeError as caught:
        error = caught
    finally:
        setattr(dataclasses, entry, original)
    assert error is not None and calls == []
    assert copy_preparation_observation(row) == dataclasses.asdict(row)


def test_mutated_original_keyword_default_contents_refuse_before_factory():
    original = dataclasses.asdict.__kwdefaults__["dict_factory"]
    calls = []

    def foreign(*args):
        calls.append(True)
        return {}

    dataclasses.asdict.__kwdefaults__["dict_factory"] = foreign
    error = None
    try:
        copy_preparation_observation(_observation())
    except TypeError as caught:
        error = caught
    finally:
        dataclasses.asdict.__kwdefaults__["dict_factory"] = original
    assert error is not None and calls == []


def _closure_value(function, name):
    return dict(
        zip(
            function.__code__.co_freevars,
            (cell.cell_contents for cell in function.__closure__),
            strict=True,
        )
    )[name]


@pytest.mark.parametrize("entry", ["check", "walk", "converter"])
def test_private_dispatch_code_substitution_is_not_executed(entry):
    if entry == "converter":
        target = _closure_value(
            _closure_value(copy_preparation_observation, "walk"), "converters"
        )[0][2]
    else:
        target = _closure_value(copy_preparation_observation, entry)
    original = target.__code__
    calls = []
    # Match free-variable arity so replacing code is a valid Python operation.
    code = "def outer():\n" + "".join(
        f"    free{i}=None\n" for i in range(len(original.co_freevars))
    )
    code += "    def foreign(*args,**kwargs):\n"
    code += (
        "        held=("
        + ",".join(f"free{i}" for i in range(len(original.co_freevars)))
        + ",)\n"
        if original.co_freevars
        else "        held=()\n"
    )
    code += "        raise AssertionError('foreign dispatcher executed')\n    return foreign\n"
    scope = {}
    exec(compile(code, "<copy-poison>", "exec"), {}, scope)  # noqa: S102 -- test-only fixed identifiers
    target.__code__ = scope["outer"]().__code__
    error = None
    try:
        copy_preparation_observation(_observation())
    except TypeError as caught:
        error = caught
    finally:
        target.__code__ = original
    assert error is not None and calls == []


def test_held_rejection_clears_only_original_copy_frames():
    class Borrowed:
        def __deepcopy__(self, memo):
            raise ValueError("held original deep-copy failure")

    row = _observation()
    object.__setattr__(row, "preparation_ref", Borrowed())
    with pytest.raises(ValueError) as caught:
        copy_preparation_observation(row)
    trace = caught.value.__traceback__
    while trace is not None:
        if (
            trace.tb_frame.f_code.co_filename.endswith(
                "repository_tree_preparation_copy.py"
            )
            or trace.tb_frame.f_code.co_filename == "<workspace-preparation-copy>"
        ):
            assert (
                not {"value", "current", "member", "result"}
                & trace.tb_frame.f_locals.keys()
            )
        trace = trace.tb_next


@pytest.mark.asyncio
async def test_original_client_preparation_observation_validation_and_release(inputs):
    _attempt, source, _observed, client, request = setup(inputs)
    plan = await client.prepare_tree_projection(request, source_delivery=source)
    observed = client.observe_tree_projection_plan(plan)
    assert (
        client.verify_tree_projection_plan(plan, expected_binding=observed.binding)
        == observed
    )
    cleanup = await client.release_tree_projection()
    assert cleanup.cleanup_state == "completed"


@pytest.mark.asyncio
@pytest.mark.parametrize("stage", ["prepare", "observe"])
@pytest.mark.parametrize(
    "substitution", ["return", "raise", "restore", "code", "defaults", "kwdefaults"]
)
async def test_central_copy_origin_is_checked_before_dispatch(
    inputs, monkeypatch, stage, substitution
):
    from aware_workspace_runtime import repository_tree_projection as runtime
    from aware_workspace_sdk.repository_tree_projection import (
        WorkspaceTreeProjectionRefusal,
    )

    _attempt, source, _observed, client, request = setup(inputs)
    plan = None
    if stage == "observe":
        plan = await client.prepare_tree_projection(request, source_delivery=source)
    original = runtime._copy_preparation_observation
    calls = []

    def foreign(*args, **kwargs):
        calls.append(True)
        if substitution == "restore":
            runtime._copy_preparation_observation = original
        if substitution == "raise":
            raise AssertionError("foreign central copier executed")
        return {}

    with monkeypatch.context() as patch:
        if substitution == "code":
            free = len(original.__code__.co_freevars)
            text = "def outer():\n" + "".join(
                f"    free{i}=None\n" for i in range(free)
            )
            text += "    def foreign(*args,**kwargs):\n"
            text += (
                "        held=(" + ",".join(f"free{i}" for i in range(free)) + ",)\n"
            )
            text += "        raise AssertionError('foreign central code executed')\n    return foreign\n"
            namespace = {}
            exec(compile(text, "<central-copy-poison>", "exec"), {}, namespace)  # noqa: S102 -- fixed test-only identifiers
            patch.setattr(original, "__code__", namespace["outer"]().__code__)
        elif substitution == "defaults":
            patch.setattr(original, "__defaults__", (None,))
        elif substitution == "kwdefaults":
            patch.setattr(original, "__kwdefaults__", {"foreign": None})
        else:
            patch.setattr(runtime, "_copy_preparation_observation", foreign)
        with pytest.raises(WorkspaceTreeProjectionRefusal):
            if stage == "prepare":
                await client.prepare_tree_projection(request, source_delivery=source)
            else:
                client.observe_tree_projection_plan(plan)
    assert calls == []
    with pytest.raises(WorkspaceTreeProjectionRefusal):
        if stage == "prepare":
            await client.prepare_tree_projection(request, source_delivery=source)
        else:
            client.observe_tree_projection_plan(plan)
    cleanup = await client.release_tree_projection()
    assert cleanup.cleanup_state == "completed"


@pytest.mark.parametrize("name", ["getattr", "type"])
@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
def test_generated_globals_never_select_native_reader(name, behavior):
    converter = _closure_value(
        _closure_value(copy_preparation_observation, "walk"), "converters"
    )[0][2]
    namespace = converter.__globals__
    previous = namespace.get(name)
    existed = name in namespace
    calls = []

    def foreign(*args):
        calls.append(True)
        if behavior == "restore":
            namespace.pop(name, None)
        if behavior == "raise":
            raise AssertionError("foreign generated global executed")

    namespace[name] = foreign
    row = _observation()
    try:
        assert copy_preparation_observation(row) == dataclasses.asdict(row)
    finally:
        if existed:
            namespace[name] = previous
        else:
            namespace.pop(name, None)
    assert calls == []


def test_held_tuple_failure_does_not_retain_unprocessed_borrowed_leaf():
    import gc
    import weakref

    class First:
        def __deepcopy__(self, memo):
            raise ValueError("early tuple failure")

    class Later:
        pass

    later = Later()
    original = _observation()
    object.__setattr__(original, "read_pins", ((First(), later),))
    reference = weakref.ref(later)
    del later
    error = None
    try:
        copy_preparation_observation(original)
    except ValueError as caught:
        error = caught
    original = None
    gc.collect()
    assert error is not None
    assert reference() is None


@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
def test_substituted_deepcopy_is_rejected_before_unknown_leaf_dispatch(behavior):
    import copy

    original = copy.deepcopy
    calls = []

    def foreign(*args, **kwargs):
        calls.append(True)
        if behavior == "restore":
            copy.deepcopy = original
        if behavior == "raise":
            raise AssertionError("foreign deepcopy selected")

    row = _observation()
    object.__setattr__(row, "preparation_ref", object())
    copy.deepcopy = foreign
    error = None
    try:
        copy_preparation_observation(row)
    except TypeError as caught:
        error = caught
    finally:
        copy.deepcopy = original
    assert error is not None and calls == []
