"""Closed A1 owner values and refusal evidence; no Issue or physical effects."""

import copy
import hashlib
import json
from dataclasses import fields, replace
from pathlib import Path
from typing import get_args, get_type_hints

import pytest
from aware_workspace_sdk import architecture_setup_admission_values as v
from aware_workspace_sdk.architecture_setup_admission_codec import (
    WorkspaceSetupValueError,
    setup_value_digest,
    setup_value_from_json,
    setup_value_from_payload,
    setup_value_to_json,
    setup_value_to_payload,
)
from tree_sitter_aware.neutral_ir import parse_neutral_aware_source

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").exists()
)
FROZEN = ROOT / "docs/reports/workspace-setup-a1-supplier-inputs-20261012.json"
SDK = Path(__file__).resolve().parents[3]
DIGEST = "sha256:" + "a" * 64


def vectors():
    absent = v.WorkspaceSetupFileObservation(
        "observed", False, None, None, None, None, None, None, None
    )
    unknown = v.WorkspaceSetupFileObservation(
        "not_observed", None, None, None, None, None, None, None, None
    )
    directory = v.WorkspaceSetupDirectoryObservation(
        "observed", True, 1, 2, 0o40755, 3, 4
    )
    ancestor = v.WorkspaceSetupAncestorGuard("src", directory)
    before = v.WorkspaceSetupInputBinding("src/body.py", absent)
    limits = v.WorkspaceSetupLimits(**dict(v.WORKSPACE_SETUP_LIMIT_CAPS))
    policy = v.WorkspaceSetupScratchPolicy(
        "prepared_once_v1",
        "retire_without_reselection",
        "original_identity_only_no_rollback",
        1,
    )
    failure = v.WorkspaceSetupPrimaryFailure("none", None, None, None, None, False)
    resource = v.WorkspaceSetupResourceEvidence(
        "resource:1",
        "workspace:1",
        "logical_keeper",
        None,
        "owned",
        False,
        "unknown",
        (),
    )
    precondition = v.WorkspaceSetupPreconditions((1, 2), (ancestor,), absent, absent)
    transition = v.WorkspaceSetupFileTransition(
        0,
        "create",
        "src/body.py",
        absent,
        DIGEST,
        12,
        "src/.aware-cas-once",
        "legacy_kernel_umask_restore_existing_v1",
    )
    step = v.WorkspaceSetupPhysicalStep(
        0,
        0,
        "scratch_create",
        "src/.aware-cas-once",
        ("src/body.py",),
        precondition,
        "legacy_kernel_umask_restore_existing_v1",
        None,
        DIGEST,
        12,
        ("resource:1",),
        ("resource:1",),
    )
    effect = v.WorkspaceSetupPhysicalEffect(
        0,
        "scratch_create",
        "src/.aware-cas-once",
        ("src/body.py",),
        "not_attempted",
        "none",
        absent,
        unknown,
        None,
        None,
        "not_confirmed",
        None,
    )
    binding = v.WorkspaceSetupPlanBinding(
        "workspace:1",
        "generation:1",
        "/tmp/example",
        (1, 2),
        "plan:1",
        "attempt:1",
        "repository",
        DIGEST,
        DIGEST,
        (before,),
        (transition,),
        (ancestor,),
        (step,),
        policy,
        limits,
        "physical:1",
        "physical-generation:1",
        "physical-preparation:1",
        1,
        2,
        "descriptor_walk_v1",
        "legacy_kernel_umask_restore_existing_v1",
    )
    observation = v.WorkspaceSetupPlanObservation(
        binding, "prepared", 0, (resource,), failure, True
    )
    cleanup = v.WorkspaceSetupCleanup(binding, "retired", (), (), "confirmed", (), True)
    client_cleanup = v.WorkspaceSetupClientCleanup(
        "workspace:1",
        "generation:1",
        "client:1",
        (),
        True,
        "confirmed",
        failure,
        (),
        True,
    )
    request = v.ArchitectureSetupRequest(
        "repository", name="example", license_expression="MIT"
    )
    receipt = v.ArchitectureSetupReceipt(
        "repository", DIGEST, "uncertain", (), ("src/body.py",), ()
    )
    result = v.WorkspaceAuthorizedSetupResult(
        binding,
        receipt,
        (),
        (step,),
        (),
        "unknown",
        "not_confirmed",
        (),
        True,
        (),
        failure,
    )
    return (
        request,
        receipt,
        result,
        ancestor,
        cleanup,
        client_cleanup,
        directory,
        absent,
        transition,
        before,
        limits,
        effect,
        step,
        binding,
        observation,
        precondition,
        failure,
        resource,
        policy,
    )


def by_name(name):
    return next(value for value in vectors() if type(value).__name__ == name)


@pytest.mark.parametrize("value", vectors(), ids=lambda value: type(value).__name__)
def test_each_original_value_roundtrips_canonically_without_live_authority(value):
    payload = setup_value_to_payload(value)
    wire = setup_value_to_json(value)
    assert wire == json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    assert setup_value_from_json(type(value), wire) == value
    assert setup_value_from_payload(type(value), payload) == value
    assert (
        setup_value_digest(value)
        == "sha256:" + hashlib.sha256(wire.encode()).hexdigest()
    )
    assert set(payload) == {"contract", "value"}


def test_fields_types_enums_and_wire_ids_match_accepted_v4_contract():
    frozen = json.loads(FROZEN.read_text())["joined_freeze"]
    for cls in v.SETUP_VALUE_TYPES:
        name = cls.__name__
        assert [field.name for field in fields(cls)] == frozen["schemas"][name]
        assert dict(v.SETUP_FIELD_TYPES[cls]) == frozen["field_types"][name]
        assert v.SETUP_SCHEMA_IDS[cls] == frozen["wire_ids"][name]
        assert set(get_type_hints(cls)) == set(frozen["schemas"][name])
    for name, members in v.SETUP_ENUMS.items():
        assert list(members) == frozen["enum_types"][name]
        assert get_args(getattr(v, name)) == members
    assert (
        dict(v.WORKSPACE_SETUP_LIMIT_CAPS)
        == frozen["limit_value_upper_bounds"]["WorkspaceSetupLimits"]
    )


def test_original_parser_reads_authored_values_without_error_or_shadow_parser():
    path = SDK / "aware/architecture_setup_admission_values.aware"
    parsed = parse_neutral_aware_source(
        path.read_text()
        + (SDK / "aware/architecture_setup_admission_errors.aware").read_text(),
        source_path=str(path),
    )

    def walk(node):
        yield node
        for child in node.children:
            yield from walk(child)

    assert not any(node.kind in ("ERROR", "MISSING") for node in walk(parsed.root))
    classes = {
        next(child.text for child in node.children if child.field_name == "name"): node
        for node in parsed.root.children
        if node.kind == "class_def"
    }
    assert set(classes) == {cls.__name__ for cls in v.SETUP_VALUE_TYPES}

    def authored_type(kind):
        if kind.startswith("Nullable["):
            return authored_type(kind[9:-1]) + "?"
        if kind.startswith("Array["):
            return authored_type(kind[6:-1]) + "[]"
        if kind == "Identity":
            return "Int[]"
        if kind in ("U64", "I64"):
            return "Int"
        if kind == "Bool":
            return "Bool"
        if kind in (
            "Code",
            "Diagnostic",
            "Digest",
            "Ref",
            "RelativePath",
            "ResourcePath",
            "RootPath",
            "RequestText",
        ):
            return "String"
        return kind

    for cls in v.SETUP_VALUE_TYPES:
        attributes = {
            next(
                child.text for child in node.children if child.field_name == "name"
            ): next(child.text for child in node.children if child.field_name == "type")
            for node in classes[cls.__name__].children
            if node.kind == "attr_def"
        }
        assert attributes == {
            name: authored_type(kind) for name, kind in v.SETUP_FIELD_TYPES[cls]
        }


@pytest.mark.parametrize("field", tuple(v.WORKSPACE_SETUP_LIMIT_CAPS))
@pytest.mark.parametrize("bad", (0, -1, True, (), []))
def test_numeric_limit_regression_refuses_boolean_arrays_and_nonpositive_caps(
    field, bad
):
    value = replace(by_name("WorkspaceSetupLimits"), **{field: bad})
    with pytest.raises(WorkspaceSetupValueError):
        setup_value_to_payload(value)


@pytest.mark.parametrize("field", tuple(v.WORKSPACE_SETUP_LIMIT_CAPS))
def test_limits_refuse_each_owner_ceiling_plus_one(field):
    value = replace(
        by_name("WorkspaceSetupLimits"),
        **{field: v.WORKSPACE_SETUP_LIMIT_CAPS[field] + 1},
    )
    with pytest.raises(WorkspaceSetupValueError, match="frozen_limit_exceeded"):
        setup_value_to_json(value)


@pytest.mark.parametrize("value", vectors(), ids=lambda value: type(value).__name__)
@pytest.mark.parametrize(
    "change", ("extra", "missing", "wrong_contract", "old_wrapper")
)
def test_closed_wrappers_refuse_schema_downgrade_or_incomplete_fields(value, change):
    payload = setup_value_to_payload(value)
    if change == "extra":
        payload["value"]["unexpected"] = None
    elif change == "missing":
        payload["value"].pop(next(iter(payload["value"])))
    elif change == "wrong_contract":
        payload["contract"] += "-old"
    else:
        payload["unexpected"] = None
    with pytest.raises(WorkspaceSetupValueError):
        setup_value_from_payload(type(value), payload)


@pytest.mark.parametrize(
    "path",
    (
        "../body",
        "/body",
        "a//b",
        "a/./b",
        "a/../b",
        "a\\b",
        "a/*",
        "e\u0301/file",
        "a\x00b",
        "a\nb",
        "a/",
    ),
)
def test_relative_paths_refuse_before_encoding_or_receipt_delivery(path):
    value = replace(by_name("WorkspaceSetupInputBinding"), path=path)
    with pytest.raises(WorkspaceSetupValueError):
        setup_value_to_payload(value)


@pytest.mark.parametrize(
    "source",
    (
        "\ufeff{}",
        '{"contract":NaN,"value":{}}',
        '{"contract":"x","contract":"x","value":{}}',
        '{"contract":"x","value":{"x":"\\ud800"}}',
        "[[[[[[",
        42,
        b"{}",
    ),
)
def test_json_refuses_duplicate_keys_nonfinite_invalid_utf8_and_foreign_source(source):
    with pytest.raises(WorkspaceSetupValueError):
        setup_value_from_json(v.WorkspaceSetupPrimaryFailure, source)


@pytest.mark.parametrize(
    "field",
    ("device", "inode", "mode", "mtime_ns", "ctime_ns", "size_bytes", "content_sha256"),
)
def test_absence_does_not_invent_identity_or_digest(field):
    value = by_name("WorkspaceSetupFileObservation")
    changed = DIGEST if field == "content_sha256" else 1
    with pytest.raises(WorkspaceSetupValueError, match="absence_has_no_identity"):
        setup_value_to_payload(replace(value, **{field: changed}))


def test_not_observed_and_no_failure_remain_honest():
    value = replace(
        by_name("WorkspaceSetupFileObservation"), state="not_observed", exists=True
    )
    with pytest.raises(WorkspaceSetupValueError, match="invented_observation"):
        setup_value_to_payload(value)
    failure = replace(by_name("WorkspaceSetupPrimaryFailure"), owner_ref="owner:1")
    with pytest.raises(WorkspaceSetupValueError, match="invented_primary_failure"):
        setup_value_to_payload(failure)


def test_request_and_diagnostic_byte_budgets_are_actual_utf8():
    value = v.ArchitectureSetupRequest("repository", dependencies=("東京" * 1000,) * 12)
    with pytest.raises(WorkspaceSetupValueError, match="encoded_byte_limit"):
        setup_value_to_json(value)
    value = replace(by_name("WorkspaceSetupResourceEvidence"), diagnostics=("é" * 129,))
    with pytest.raises(WorkspaceSetupValueError, match="string_limit"):
        setup_value_to_json(value)
    with pytest.raises(WorkspaceSetupValueError, match="array_limit"):
        setup_value_to_json(replace(value, diagnostics=("fixed",) * 9))


def test_exact_request_byte_ceiling_and_refusal_before_full_encoding(monkeypatch):
    from aware_workspace_sdk import architecture_setup_admission_codec as codec

    base = v.ArchitectureSetupRequest("repository", dependencies=("",) * 8)
    overhead = len(setup_value_to_json(base).encode("utf-8"))
    last = 65536 - overhead - 7 * 8192
    exact = replace(base, dependencies=("x" * 8192,) * 7 + ("x" * last,))
    assert len(setup_value_to_json(exact).encode("utf-8")) == 65536
    assert setup_value_from_json(type(exact), setup_value_to_json(exact)) == exact
    calls = []
    monkeypatch.setattr(codec, "_wire", lambda *_: calls.append("full_encoding"))
    over = replace(exact, dependencies=(*exact.dependencies[:-1], "x" * (last + 1)))
    with pytest.raises(WorkspaceSetupValueError, match="encoded_byte_limit"):
        setup_value_to_payload(over)
    assert calls == []


def test_nested_wrapper_downgrade_and_ordinal_change_refuse():
    binding = by_name("WorkspaceSetupPlanBinding")
    payload = setup_value_to_payload(binding)
    payload["value"]["limits"]["value"]["file_transitions"] = True
    with pytest.raises(WorkspaceSetupValueError, match="exact_integer_required"):
        setup_value_from_payload(type(binding), payload)
    row = replace(binding.ordered_effects[0], ordinal=1)
    with pytest.raises(WorkspaceSetupValueError, match="ordered_ordinals_required"):
        setup_value_to_json(replace(binding, ordered_effects=(row,)))


def test_hostile_native_and_slot_substitution_dispatch_zero_foreign_calls(monkeypatch):
    calls = []

    class Foreign:
        def __getattribute__(self, key):
            calls.append(key)
            raise AssertionError("foreign_dispatch")

    with pytest.raises(WorkspaceSetupValueError):
        setup_value_to_payload(Foreign())
    cls = v.WorkspaceSetupResourceEvidence
    original = vars(cls)["path"]
    monkeypatch.setattr(cls, "path", property(lambda _: calls.append("path")))
    with pytest.raises(WorkspaceSetupValueError, match="original_slot_changed"):
        setup_value_to_payload(object.__new__(cls))
    monkeypatch.setattr(cls, "path", original)
    assert calls == []


def test_decode_bypasses_replaced_constructor_without_dispatch(monkeypatch):
    value = by_name("WorkspaceSetupPrimaryFailure")
    payload = setup_value_to_payload(value)
    calls = []
    monkeypatch.setattr(type(value), "__init__", lambda *_: calls.append("constructor"))
    decoded = setup_value_from_payload(type(value), payload)
    assert decoded == value
    assert calls == []


def test_repeated_decoding_has_no_opaque_owner_or_replay_permission():
    value = by_name("WorkspaceSetupPlanBinding")
    payload = setup_value_to_payload(value)
    first = setup_value_from_payload(type(value), copy.deepcopy(payload))
    second = setup_value_from_payload(type(value), copy.deepcopy(payload))
    assert first == second == value
    assert first is not second
    assert not hasattr(first, "apply")
