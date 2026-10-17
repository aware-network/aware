"""Fresh primitive receipt iteration keeps predecessor behavior and wire bytes."""

from __future__ import annotations

import hashlib
import subprocess
import types
from pathlib import Path

import pytest
from aware_workspace_runtime import change_evidence_codec as codec


@pytest.fixture(scope="module")
def predecessor():
    root = next(
        p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").exists()
    )
    path = "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/change_evidence_codec.py"
    body = subprocess.run(
        ["git", "show", "8be9c5aa6dcfa7dceb6b6aebb14f2fcbdae35bc7:" + path],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    assert (
        hashlib.sha256(body).hexdigest()
        == "063d3330bbf45793163354b3e920335b8989c3d6af3b09f139d4e9fa683bf732"
    )
    module = types.ModuleType("aware_workspace_runtime._aggregate_receipt_predecessor")
    module.__package__ = "aware_workspace_runtime"
    exec(compile(body, "<literal-receipt-predecessor>", "exec"), vars(module))  # noqa: S102
    return module


@pytest.mark.parametrize("scalar", [str, int, bool])
@pytest.mark.parametrize(
    "members", [(), (None,), ("a", None, "é"), (1, -1, 2**64), (False, True)]
)
def test_exact_primitive_tuple_result_and_member_identity(predecessor, scalar, members):
    actual = codec._encode(members, tuple[scalar, ...])
    expected = predecessor._encode(members, tuple[scalar, ...])
    assert actual == expected
    assert all(a is b for a, b in zip(actual, expected, strict=True))


@pytest.mark.parametrize("module_name", ["candidate", "predecessor"])
@pytest.mark.parametrize("failure", [False, True])
def test_primitive_iteration_does_not_add_length_hint_or_coercion(
    predecessor, module_name, failure
):
    module = codec if module_name == "candidate" else predecessor
    calls = []

    class Members:
        def __iter__(self):
            calls.append("iter")
            yield "first"
            calls.append("second")
            if failure:
                raise OSError("original iterator interruption")
            yield None

        def __len__(self):
            raise AssertionError("must not ask length")

        def __length_hint__(self):
            raise AssertionError("must not ask length hint")

    if failure:
        with pytest.raises(OSError, match="original iterator interruption"):
            module._encode(Members(), tuple[str, ...])
    else:
        assert module._encode(Members(), tuple[str, ...]) == ["first", None]
    assert calls == ["iter", "second"]


def test_primitive_members_are_reread_after_prior_encoding(predecessor):
    members = ["original"]
    assert codec._encode(members, tuple[str, ...]) == predecessor._encode(
        members, tuple[str, ...]
    )
    members[0] = "changed"
    assert codec._encode(members, tuple[str, ...]) == ["changed"]


@pytest.mark.parametrize(
    "field", ["result_coordinate", "context_refs", "expected_coordinate"]
)
@pytest.mark.parametrize("bad", [None, False, "foreign", (), ("new", None), 7])
def test_compiled_nullable_and_tuple_fields_preserve_original_fallback(
    predecessor, field, bad
):
    import copy

    from test_change_evidence_codec import _mutation_receipt

    value = copy.copy(_mutation_receipt())
    object.__setattr__(value, field, bad)
    outputs = []
    for module in (codec, predecessor):
        try:
            outputs.append(("ok", module.repository_mutation_receipt_payload(value)))
        except (ValueError, TypeError, AttributeError, KeyError) as error:
            outputs.append((type(error).__name__, str(error)))
    assert outputs[0] == outputs[1]


def test_closed_nullable_record_and_primitive_tuple_skip_generic_reflection(
    monkeypatch, predecessor
):
    from test_change_evidence_codec import _mutation_receipt

    calls = []
    original = codec._encode_union

    def observe(value, hint):
        calls.append(hint)
        return original(value, hint)

    monkeypatch.setattr(codec, "_encode_union", observe)
    value = _mutation_receipt()
    assert codec.repository_mutation_receipt_payload(
        value
    ) == predecessor.repository_mutation_receipt_payload(value)
    assert not calls


@pytest.fixture
def dispatch_predecessor():
    root = next(
        p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").exists()
    )
    path = "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/change_evidence_codec.py"
    body = subprocess.run(
        ["git", "show", "1296ab5d530:" + path],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    assert (
        hashlib.sha256(body).hexdigest()
        == "9f8a5bc367ce79e8abeb7a357c44e58dc8e22488f358202259788ead5775f03e"
    )
    module = types.ModuleType("aware_workspace_runtime._dispatch_predecessor")
    module.__package__ = "aware_workspace_runtime"
    exec(compile(body, "<literal-dispatch-predecessor>", "exec"), vars(module))  # noqa: S102
    return module


def test_exact_records_skip_generic_reflection_without_skipping_lazy_hints(
    monkeypatch, dispatch_predecessor
):
    from test_change_evidence_codec import _mutation_receipt

    reflected = []
    hints = []
    original_origin, original_hints = codec.get_origin, codec._type_hints

    def origin(annotation):
        entry = codec._RECEIPT_ORIGINAL_ENTRIES.get(id(annotation))
        if entry is not None and entry[0] is annotation:
            reflected.append(annotation)
        return original_origin(annotation)

    def read_hints(annotation):
        hints.append(annotation)
        return original_hints(annotation)

    monkeypatch.setattr(codec, "get_origin", origin)
    monkeypatch.setattr(codec, "_type_hints", read_hints)
    value = _mutation_receipt()
    assert codec.repository_mutation_receipt_payload(
        value
    ) == dispatch_predecessor.repository_mutation_receipt_payload(value)
    assert hints
    assert type(value) in hints
    assert not reflected


@pytest.mark.parametrize("warm", [False, True])
def test_early_record_dispatch_preserves_cold_and_warm_annotation_history(
    monkeypatch, dispatch_predecessor, warm
):
    from test_change_evidence_codec import _mutation_receipt

    module = types.ModuleType("aware_workspace_runtime._dispatch_cold_candidate")
    module.__package__ = "aware_workspace_runtime"
    body = Path(codec.__file__).read_bytes()
    exec(compile(body, "<dispatch-cold-candidate>", "exec"), vars(module))  # noqa: S102
    modules = (dispatch_predecessor, module)
    value = _mutation_receipt()
    for item in modules:
        assert item._type_hints.cache_info().currsize == 0
        if warm:
            item.repository_mutation_receipt_payload(value)
    monkeypatch.setitem(type(value).__annotations__, "target_path", tuple[str, ...])
    payloads = [item.repository_mutation_receipt_payload(value) for item in modules]
    assert payloads[0] == payloads[1]
    assert payloads[0]["value"]["target_path"] == (
        value.target_path if warm else list(value.target_path)
    )


def test_removed_dataclass_metadata_keeps_original_refusal(
    monkeypatch, dispatch_predecessor
):
    from test_change_evidence_codec import _mutation_receipt

    value = _mutation_receipt()
    monkeypatch.delattr(type(value), "__dataclass_fields__")
    refusals = []
    for module in (dispatch_predecessor, codec):
        with pytest.raises(TypeError) as error:
            module._encode(value, type(value))
        refusals.append(str(error.value))
    assert refusals[0] == refusals[1]


@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
def test_early_dispatch_rejects_foreign_registry_before_lookup(monkeypatch, behavior):
    from test_change_evidence_codec import _mutation_receipt

    original = codec._RECEIPT_ORIGINAL_ENTRIES
    calls = []

    class Foreign(dict):
        def get(self, *args):
            calls.append(args)
            if behavior == "raise":
                raise AssertionError("foreign registry lookup must not execute")
            if behavior == "restore":
                monkeypatch.setattr(codec, "_RECEIPT_ORIGINAL_ENTRIES", original)
            return original.get(*args)

    monkeypatch.setattr(codec, "_RECEIPT_ORIGINAL_ENTRIES", Foreign(original))
    with pytest.raises(TypeError, match="Original receipt compiler registry"):
        codec.repository_mutation_receipt_payload(_mutation_receipt())
    assert calls == []


@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
def test_early_dispatch_rejects_foreign_converter_before_execution(
    monkeypatch, behavior
):
    from test_change_evidence_codec import _mutation_receipt

    value = _mutation_receipt()
    registry = codec._RECEIPT_FIELDS_BY_ID
    original = registry[id(type(value))]
    calls = []

    def foreign(*args):
        calls.append(args)
        if behavior == "raise":
            raise AssertionError("foreign converter must not execute")
        if behavior == "restore":
            monkeypatch.setitem(registry, id(type(value)), original)
        return {}

    monkeypatch.setitem(
        registry,
        id(type(value)),
        (original[0], original[1], (foreign, foreign.__code__), *original[3:]),
    )
    with pytest.raises(TypeError, match="Original receipt compiler entry"):
        codec.repository_mutation_receipt_payload(value)
    assert calls == []
