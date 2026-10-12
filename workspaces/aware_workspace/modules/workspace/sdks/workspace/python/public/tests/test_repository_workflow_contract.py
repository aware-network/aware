"""Real authored lowering and portable evidence boundaries; no effect authority."""

from __future__ import annotations

import dataclasses
import subprocess
import sys
import tomllib
import types
from pathlib import Path
from typing import Literal, get_args, get_origin, get_type_hints

import pytest
from aware_workspace_sdk import repository_workflow_codec as codec
from aware_workspace_sdk import repository_workflow_values as values
from aware_workspace_sdk.repository_workflow import WorkspaceRepositoryWorkflowPlan
from tree_sitter_aware.neutral_ir import parse_neutral_aware_source
from tree_sitter_aware.ontology_meaning import meaning_value_to_json
from tree_sitter_aware.ontology_meaning_resolver import (
    OntologyMeaningPackageInput,
    resolve_ontology_meaning,
)

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").is_file()
)
SDK = ROOT / "workspaces/aware_workspace/modules/workspace/sdks/workspace/aware"
ENUMS = {
    name: getattr(values, name)
    for name in values.__all__
    if get_origin(getattr(values, name)) is Literal
}
ERROR = codec.WorkspaceWorkflowValueError


def sample(annotation, *, nulls=False):
    origin, args = get_origin(annotation), get_args(annotation)
    if origin is types.UnionType:
        return None if nulls else sample(args[0], nulls=nulls)
    if annotation is str:
        return "descriptive:é"
    if annotation is int:
        return 17
    if annotation is bool:
        return not nulls
    if origin is Literal:
        return args[0]
    if origin is tuple:
        return (sample(args[0], nulls=nulls),)
    hints = get_type_hints(annotation)
    return annotation(
        **{
            f.name: sample(hints[f.name], nulls=nulls)
            for f in dataclasses.fields(annotation)
        }
    )


@pytest.fixture(scope="module")
def meaning():
    manifest = tomllib.loads((SDK / "aware.sdk.toml").read_text())["sdk"]
    sources = (
        "repository_workflow_values.aware",
        "repository_publication_values.aware",
        "repository_publication_ports.aware",
        "repository_source_projection_values.aware",
    )
    documents = tuple(
        parse_neutral_aware_source(
            (SDK / name).read_text(),
            source_path="/sdk/workspace/" + name,
        )
        for name in sources
    )
    return resolve_ontology_meaning(
        (
            OntologyMeaningPackageInput(
                package_name=manifest["package_name"],
                fqn_prefix=manifest["fqn_prefix"],
                sources_root="/sdk/workspace",
                dependencies=(),
                documents=documents,
                namespace_by_source_path=tuple((d.source_path, "") for d in documents),
            ),
        ),
        selected_package_names=frozenset({manifest["package_name"]}),
    )


@pytest.mark.parametrize("record", values.WORKFLOW_VALUE_TYPES)
def test_authored_fields_match_real_combined_lowering(meaning, record):
    members = {
        e.fqn.rsplit(".", 1)[1]: meaning_value_to_json(e.payload)
        for e in meaning.entries
        if e.kind == "member"
        and e.fqn.rsplit(".", 1)[0] == "aware_workspace_sdk." + record.__name__
    }
    hints = get_type_hints(record)
    assert set(members) == set(hints)
    for index, field in enumerate(dataclasses.fields(record)):
        hint = hints[field.name]
        nullable = get_origin(hint) is types.UnionType
        if nullable:
            hint = next(arg for arg in get_args(hint) if arg is not type(None))
        collection = get_origin(hint) is tuple
        if collection:
            hint = get_args(hint)[0]
        member = members[field.name]
        assert (member["position"], member["nullable"], member["collection"]) == (
            index,
            nullable,
            collection,
        )
        assert member["identity_key"] is False
        spelling = member["type_expression"].removesuffix("?").removesuffix("[]")
        if get_origin(hint) is Literal:
            assert ENUMS[spelling] is hint
        elif hint in (str, int, bool):
            assert spelling == {str: "String", int: "Int", bool: "Bool"}[hint]
        else:
            assert member["target_fqn"] == "aware_workspace_sdk." + hint.__name__


@pytest.mark.parametrize("name", tuple(ENUMS))
def test_authored_enum_order_is_exact(meaning, name):
    entries = sorted(
        (
            e
            for e in meaning.entries
            if e.kind == "enum_option"
            and e.fqn.rsplit(".", 1)[0] == "aware_workspace_sdk." + name
        ),
        key=lambda e: meaning_value_to_json(e.payload)["position"],
    )
    assert tuple(e.fqn.rsplit(".", 1)[1] for e in entries) == get_args(ENUMS[name])


@pytest.mark.parametrize("record", values.WORKFLOW_VALUE_TYPES)
@pytest.mark.parametrize("nulls", (False, True))
def test_all_values_round_trip_as_detached_records(record, nulls):
    original = sample(record, nulls=nulls)
    decoded = codec.repository_workflow_value_from_json(
        record, codec.repository_workflow_value_to_json(original)
    )
    assert decoded == original and decoded is not original
    assert codec.repository_workflow_value_to_payload(
        decoded
    ) == codec.repository_workflow_value_to_payload(original)


def test_exact_integer_over_float_precision_is_preserved():
    original = values.WorkspaceWorkflowEvidenceReference(
        "owner", "receipt", "sha256:" + "a" * 64, 2**64
    )
    encoded = codec.repository_workflow_value_to_json(original)
    assert "18446744073709551616" in encoded
    assert (
        codec.repository_workflow_value_from_json(type(original), encoded).size_bytes
        == 2**64
    )


@pytest.mark.parametrize(
    "text",
    (
        "{",
        '{"key":"a","key":"b","value":"v"}',
        '{"key":NaN,"value":"v"}',
        '{"key":1.0,"value":"v"}',
        "[" * 2000 + "]" * 2000,
        '"' + "a" * (1024 * 1024) + '"',
    ),
)
def test_bad_json_refuses(text):
    with pytest.raises(ERROR):
        codec.repository_workflow_value_from_json(values.WorkspaceWorkflowMarker, text)


@pytest.mark.parametrize(
    "change", ({"extra": 1}, {"key": True}, {"value": "\ud800"}, {"key": "x" * 16385})
)
def test_record_shape_and_text_bounds(change):
    payload = {"key": "key", "value": "value", **change}
    with pytest.raises(ERROR):
        codec.repository_workflow_value_from_payload(
            values.WorkspaceWorkflowMarker, payload
        )


@pytest.mark.parametrize(
    "field,count",
    (
        ("artifact_bindings", 65),
        ("request_refs", 17),
        ("result_refs", 17),
        ("error_refs", 17),
        ("diagnostics", 257),
    ),
)
def test_evidence_groups_are_bounded(field, count):
    value = sample(values.WorkspaceRepositoryWorkflowEvidenceAppendRequest)
    changed = dataclasses.replace(value, **{field: getattr(value, field) * count})
    with pytest.raises(ERROR):
        codec.repository_workflow_value_to_json(changed)


def test_effect_is_preserved_despite_unknown_persistence_and_cleanup():
    original = dataclasses.replace(
        sample(values.WorkspaceRepositoryWorkflowEvidenceWriteObservation),
        effect_state="applied",
        persistence_state="unknown",
        cleanup_state="incomplete",
    )
    assert (
        codec.repository_workflow_value_from_json(
            type(original), codec.repository_workflow_value_to_json(original)
        )
        == original
    )
    undispatched = dataclasses.replace(
        sample(values.WorkspaceRepositoryWorkflowEvidenceAppendRequest),
        effect_state="applied",
    )
    with pytest.raises(ERROR):
        codec.repository_workflow_value_to_json(undispatched)


def test_exact_collections_and_numeric_types_required():
    value = sample(values.WorkspaceRepositoryWorkflowEvidenceAppendRequest)
    for changes in (
        {"expected_cursor": True},
        {"expected_cursor": -1},
        {"expected_cursor": 2**64 + 1},
        {"expected_cursor": 257},
        {"request_refs": []},
    ):
        with pytest.raises(ERROR):
            codec.repository_workflow_value_to_json(
                dataclasses.replace(value, **changes)
            )


def test_foreign_values_and_metaclasses_have_no_behavior():
    calls = []

    class Meta(type):
        def __eq__(cls, other):
            calls.append("class equality")
            raise AssertionError

    class Foreign(metaclass=Meta):
        def __getattribute__(self, name):
            calls.append("attribute")
            raise AssertionError

    for obj in (Foreign(), object.__new__(WorkspaceRepositoryWorkflowPlan)):
        with pytest.raises(ERROR):
            codec.repository_workflow_value_to_json(obj)
    with pytest.raises(ERROR):
        codec.repository_workflow_value_from_payload(Foreign, {})
    assert calls == []


def test_hostile_slot_substitution_has_zero_calls(monkeypatch):
    original = values.WorkspaceWorkflowMarker("key", "value")
    calls = []

    class Descriptor:
        def __get__(self, instance, owner):
            calls.append(True)
            raise AssertionError

    monkeypatch.setattr(values.WorkspaceWorkflowMarker, "key", Descriptor())
    with pytest.raises(ERROR):
        codec.repository_workflow_value_to_json(original)
    with pytest.raises(ERROR):
        codec.repository_workflow_value_from_payload(
            type(original), {"key": "key", "value": "value"}
        )
    assert calls == []


def test_descriptive_imports_select_no_runtime_or_service():
    script = """
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(("aware_workspace_runtime", "aware_workspace_fs_adapter", "aware_issue", "aware_meta", "aware_service", "aware_local_dev")):
            raise AssertionError("unexpected owner import: " + fullname)
sys.meta_path.insert(0, Block())
from aware_workspace_sdk import repository_workflow_values as v, repository_workflow_codec as c
from aware_workspace_sdk.repository_workflow import WorkspaceRepositoryWorkflowClient
assert c.repository_workflow_value_from_json(v.WorkspaceWorkflowMarker, '{"key":"k","value":"v"}').key == "k"
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_only_descriptive_roots_are_exported_and_schema_is_registered():
    assert len(values.WORKFLOW_VALUE_TYPES) == 12 and len(ENUMS) == 11
    manifest = tomllib.loads((SDK / "aware.sdk.toml").read_text())
    assert manifest["build"]["include_paths"] == ["*.aware"]
    assert not any(
        "Plan" == root.__name__ or "Attempt" == root.__name__
        for root in values.WORKFLOW_VALUE_TYPES
    )


def test_aggregate_attempt_limit_preserves_each_individual_record_limit():
    record = dataclasses.replace(
        sample(values.WorkspaceRepositoryWorkflowEvidenceAppendRequest),
        diagnostics=("x" * 8192,) * 96,
    )
    record_text = codec.repository_workflow_value_to_json(record)
    assert len(record_text.encode()) < codec.MAX_WORKFLOW_RECORD_BYTES
    attempt = dataclasses.replace(
        sample(values.WorkspaceRepositoryWorkflowAttemptObservation),
        records=(record, record),
    )
    encoded = codec.repository_workflow_value_to_json(attempt)
    assert len(encoded.encode()) > codec.MAX_WORKFLOW_RECORD_BYTES
    assert codec.repository_workflow_value_from_json(type(attempt), encoded) == attempt
    excessive = dataclasses.replace(record, diagnostics=("x" * 16384,) * 65)
    with pytest.raises(ERROR):
        codec.repository_workflow_value_to_json(
            dataclasses.replace(attempt, records=(excessive,))
        )


def test_workflow_refusal_preserves_uncertain_persistence_and_cleanup():
    from aware_workspace_sdk.repository_workflow import (
        WorkspaceRepositoryWorkflowRefusal,
    )

    refusal = WorkspaceRepositoryWorkflowRefusal(
        "evidence_persistence_unknown",
        stage="evidence_closeout",
        persistence="unknown",
        cleanup="incomplete",
        diagnostics=("journal_write_unknown",),
    )
    evidence = codec.repository_workflow_value_from_json(
        values.WorkspaceRepositoryWorkflowRefusalEvidence,
        codec.repository_workflow_value_to_json(refusal.evidence),
    )
    assert (
        evidence.persistence_state == "unknown"
        and evidence.cleanup.state == "incomplete"
    )
    assert evidence.stage == "evidence_closeout"


def test_persisted_values_cannot_reconstruct_original_attempt():
    from aware_workspace_sdk.repository_workflow import (
        WorkspaceRepositoryWorkflowAttempt,
    )

    handle = object.__new__(WorkspaceRepositoryWorkflowAttempt)
    with pytest.raises(ERROR):
        codec.repository_workflow_value_to_payload(handle)
    with pytest.raises(ERROR):
        codec.repository_workflow_value_from_payload(
            WorkspaceRepositoryWorkflowAttempt, {}
        )
