"""Workspace production value parity, not provider or writer qualification."""

from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
import tomllib
import types
from pathlib import Path
from typing import Literal, get_args, get_origin, get_type_hints

import pytest
from aware_workspace_sdk import repository_publication as public
from aware_workspace_sdk.repository_publication import codec, values
from tree_sitter_aware.neutral_ir import parse_neutral_aware_source
from tree_sitter_aware.ontology_meaning import meaning_value_to_json
from tree_sitter_aware.ontology_meaning_resolver import (
    OntologyMeaningPackageInput,
    resolve_ontology_meaning,
)

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "aware.repo.toml").is_file()
)
AUTHORED = ROOT / "workspaces/aware_workspace/modules/workspace/sdks/workspace/aware"


def sample(annotation, *, nulls=False):
    origin, arguments = get_origin(annotation), get_args(annotation)
    if origin is types.UnionType:
        return None if nulls else sample(arguments[0], nulls=nulls)
    if annotation is str:
        return "évidence"
    if annotation is int:
        return 2**63 + 19
    if annotation is bool:
        return not nulls
    if origin is Literal:
        return arguments[-1] if nulls else arguments[0]
    if annotation == tuple[int, int]:
        return (19, 29)
    if annotation == list[list[str]]:
        return [["git", "-C", "a b", "é"], [], ["diff", "--", "a"]]
    if origin in (tuple, list):
        result = [sample(arguments[0], nulls=nulls)]
        return tuple(result) if origin is tuple else result
    hints = get_type_hints(annotation)
    return annotation(
        **{
            field.name: ("a", "é.txt")
            if field.name == "target_paths"
            else sample(hints[field.name], nulls=nulls)
            for field in dataclasses.fields(annotation)
        }
    )


def lower(source: str | None = None):
    manifest = tomllib.loads((AUTHORED / "aware.sdk.toml").read_text())
    path = "/sdk/workspace/repository_publication_values.aware"
    document = parse_neutral_aware_source(
        (AUTHORED / "repository_publication_values.aware").read_text()
        if source is None
        else source,
        source_path=path,
    )
    package = manifest["sdk"]
    return resolve_ontology_meaning(
        (
            OntologyMeaningPackageInput(
                package_name=package["package_name"],
                fqn_prefix=package["fqn_prefix"],
                sources_root="/sdk/workspace",
                dependencies=(),
                documents=(document,),
                namespace_by_source_path=((path, ""),),
            ),
        ),
        selected_package_names=frozenset({package["package_name"]}),
    )


@pytest.mark.parametrize("record", values.PUBLICATION_VALUE_TYPES)
@pytest.mark.parametrize("nulls", [False, True])
def test_every_production_value_round_trips_without_input_mutation(record, nulls):
    original = sample(record, nulls=nulls)
    payload = codec.repository_publication_value_to_payload(original)
    saved = json.dumps(payload, ensure_ascii=False)
    decoded = codec.repository_publication_value_from_payload(record, payload)
    assert decoded == original
    assert type(decoded) is record
    assert json.dumps(payload, ensure_ascii=False) == saved
    assert (
        codec.repository_publication_value_from_json(
            record, codec.repository_publication_value_to_json(original)
        )
        == original
    )


@pytest.mark.parametrize("record", values.PUBLICATION_VALUE_TYPES)
def test_each_value_refuses_missing_and_extra_fields_without_mutation(record):
    payload = codec.repository_publication_value_to_payload(sample(record))
    missing = dict(payload)
    missing.pop(next(iter(missing)))
    extra = dict(payload, restore_authority=True)
    for invalid in (missing, extra):
        saved = json.dumps(invalid, ensure_ascii=False)
        with pytest.raises(codec.WorkspacePublicationValueError):
            codec.repository_publication_value_from_payload(record, invalid)
        assert json.dumps(invalid, ensure_ascii=False) == saved


@pytest.mark.parametrize("record", values.PUBLICATION_VALUE_TYPES)
def test_python_fields_match_real_lowered_production_owner_types(record):
    meaning = lower()
    prefix = tomllib.loads((AUTHORED / "aware.sdk.toml").read_text())["sdk"][
        "fqn_prefix"
    ]
    owner = prefix + "." + record.__name__
    members = {
        entry.fqn.rsplit(".", 1)[1]: meaning_value_to_json(entry.payload)
        for entry in meaning.entries
        if entry.kind == "member" and entry.fqn.rsplit(".", 1)[0] == owner
    }
    hints = get_type_hints(record)
    definitions = dataclasses.fields(record)
    assert set(members) == set(hints)
    for position, field in enumerate(definitions):
        annotation = hints[field.name]
        nullable = get_origin(annotation) is types.UnionType
        if nullable:
            annotation = next(
                item for item in get_args(annotation) if item is not type(None)
            )
        payload = members[field.name]
        assert payload["position"] == position
        assert payload["nullable"] is nullable
        spelling = payload["type_expression"].removesuffix("?")
        if get_origin(annotation) is Literal:
            entries = [
                entry
                for entry in meaning.entries
                if entry.kind == "enum_option"
                and entry.fqn.rsplit(".", 1)[0] == prefix + "." + spelling
            ]
            options = [
                entry.fqn.rsplit(".", 1)[1]
                for entry in sorted(
                    entries,
                    key=lambda entry: meaning_value_to_json(entry.payload)["position"],
                )
            ]
            assert tuple(options) == get_args(annotation)
        elif annotation == tuple[int, int]:
            assert spelling == "WorkspaceFileIdentity"
        elif annotation == list[list[str]]:
            assert spelling == "WorkspaceGitCommand[]"
        elif get_origin(annotation) in (tuple, list):
            item = get_args(annotation)[0]
            assert spelling == (
                {str: "String"}.get(item, getattr(item, "__name__", "")) + "[]"
            )
        else:
            assert spelling == {str: "String", int: "Int", bool: "Bool"}.get(
                annotation, getattr(annotation, "__name__", "")
            )


def test_sdk_manifest_selects_production_source_without_metadata_changes():
    manifest = tomllib.loads((AUTHORED / "aware.sdk.toml").read_text())
    assert "*.aware" in manifest["build"]["include_paths"]
    assert manifest["sdk"]["fqn_prefix"] == "aware_workspace_sdk"
    assert len(lower().entries) == 223
    assert lower().canonical_bytes() == lower().canonical_bytes()
    fixture = (
        Path(__file__).parent / "fixtures/workspace_publication_values.aware"
    ).read_text()
    production = (AUTHORED / "repository_publication_values.aware").read_text()
    assert production.split("\n", 2)[2] == fixture.split("\n", 2)[2]


def test_actual_original_writer_report_preserves_all_32_field_types_and_values():
    from aware_workspace_operator.models import WorkspaceCommitReport

    assert len(WorkspaceCommitReport.model_fields) == 32
    assert tuple(WorkspaceCommitReport.model_fields) == tuple(
        field.name
        for field in dataclasses.fields(values.WorkspaceRepositoryWriterObservation)
    )
    hints = get_type_hints(values.WorkspaceRepositoryWriterObservation)
    assert all(
        hints[name] == field.annotation
        for name, field in WorkspaceCommitReport.model_fields.items()
    )
    original = WorkspaceCommitReport(
        repo_root="/repository/é",
        status="failed",
        commit_hash="a" * 40,
        expected_head="b" * 40,
        candidate_commit="a" * 40,
        reference_update="cas_applied",
        updated_reference="refs/heads/main",
        shared_index_projection="failed",
        shared_index_projection_error="retained cleanup error",
        index_reconciliation_pending=True,
        transaction_mode="isolated_index_atomic_ref_v1",
        command_log=[["git", "diff", "--", "é x"], []],
    )
    value = values.WorkspaceRepositoryWriterObservation(**original.model_dump())
    payload = codec.repository_publication_value_to_payload(value)
    assert payload["command_log"] == [
        {"arguments": ["git", "diff", "--", "é x"]},
        {"arguments": []},
    ]
    decoded = codec.repository_publication_value_from_json(
        type(value), codec.repository_publication_value_to_json(value)
    )
    reconstructed = WorkspaceCommitReport(**dataclasses.asdict(decoded))
    assert reconstructed.model_dump(mode="json") == original.model_dump(mode="json")
    assert decoded.commit_hash == original.commit_hash and decoded.status == "failed"


def test_identity_mapping_and_codec_collections_are_detached():
    original = sample(values.WorkspaceRepositoryPhysicalEffect)
    payload = codec.repository_publication_value_to_payload(original)
    assert payload["before_identity"] == {"device": 19, "inode": 29}
    decoded = codec.repository_publication_value_from_payload(type(original), payload)
    payload["before_identity"]["device"] = 99
    payload["diagnostics"].append("later")
    assert decoded == original and decoded.before_identity == (19, 29)
    report = sample(values.WorkspaceRepositoryWriterObservation)
    wire = codec.repository_publication_value_to_payload(report)
    wire["command_log"][0]["arguments"].append("later")
    assert report.command_log == [["git", "-C", "a b", "é"], [], ["diff", "--", "a"]]


@pytest.mark.parametrize(
    "source", ["NaN", "Infinity", "-Infinity", "1e999", "1.25", "{}", "[]", "null"]
)
def test_malformed_json_and_nonfinite_numbers_refuse(source):
    with pytest.raises(codec.WorkspacePublicationValueError):
        codec.repository_publication_value_from_json(
            values.WorkspaceRepositoryCommitRequest, source
        )


@pytest.mark.parametrize("field", ["repository_ref", "target_paths"])
def test_duplicate_json_fields_refuse(field):
    request = sample(values.WorkspaceRepositoryCommitRequest)
    payload = codec.repository_publication_value_to_payload(request)
    source = codec.repository_publication_value_to_json(request)
    duplicate = (
        source[:-1] + "," + json.dumps(field) + ":" + json.dumps(payload[field]) + "}"
    )
    with pytest.raises(codec.WorkspacePublicationValueError, match="duplicate"):
        codec.repository_publication_value_from_json(type(request), duplicate)


@pytest.mark.parametrize(
    "path",
    ["", "/a", "a\\b", ".", "..", "a/../b", "a//b", "a/", "e\u0301/a", "a\ud800"]
    + [f"a{chr(number)}b" for number in (*range(32), *range(127, 160))],
)
def test_noncanonical_paths_refuse_without_normalizing(path):
    request = values.WorkspaceRepositoryCommitRequest(
        "repo", (path,), "message", "attempt"
    )
    with pytest.raises(codec.WorkspacePublicationValueError):
        codec.repository_publication_value_to_payload(request)


@pytest.mark.parametrize("paths", [("b", "a"), ("a", "a")])
def test_unsorted_and_duplicate_paths_refuse(paths):
    with pytest.raises(codec.WorkspacePublicationValueError):
        codec.repository_publication_value_to_payload(
            values.WorkspaceRepositoryCommitRequest("repo", paths, "message", "attempt")
        )


@pytest.mark.parametrize("value", [True, 1.0, "1", None])
def test_file_identity_integer_is_strict_not_boolean_or_coerced(value):
    with pytest.raises(codec.WorkspacePublicationValueError):
        codec.repository_publication_value_from_payload(
            values.WorkspaceFileIdentity, {"device": value, "inode": 9}
        )


def test_unknown_and_missing_evidence_are_distinct_not_defaulted():
    value = sample(values.WorkspaceRepositoryCommitResult, nulls=True)
    assert value.publication_state == "unknown"
    payload = codec.repository_publication_value_to_payload(value)
    assert payload["commit_hash"] is None and payload["lock_release"] is None
    assert (
        codec.repository_publication_value_from_payload(type(value), payload) == value
    )
    del payload["lock_release"]
    with pytest.raises(codec.WorkspacePublicationValueError):
        codec.repository_publication_value_from_payload(type(value), payload)


def test_forged_type_and_handles_cannot_be_decoded_or_encoded():
    class Forged(type):
        def __eq__(self, other):
            return True

    class Handle(metaclass=Forged):
        pass

    with pytest.raises(codec.WorkspacePublicationValueError):
        codec.repository_publication_value_from_payload(Handle, {})
    with pytest.raises(codec.WorkspacePublicationValueError):
        codec.repository_publication_value_to_payload(Handle())
    for name in (
        "WorkspaceRepositoryCommitPlan",
        "WorkspacePublicationWorkAdmission",
        "WorkspacePublicationExecutionClaim",
        "publish_repository_commit",
    ):
        assert not hasattr(public, name)
    assert all(hasattr(public, name) for name in public.__all__)


def test_fresh_normal_imports_do_not_load_domain_implementations():
    source = """
import sys
import aware_workspace_sdk.repository_publication as workspace
import aware_issue_sdk.repository_publication as issue
for name in ('aware_workspace_runtime', 'aware_workspace_operator', 'aware_issue_runtime',
             'aware_issue_operational_runtime', 'aware_issue_fs_adapter', 'aware_orm',
             'aware_workspace_service_api', 'aware_workspace_service_dto', 'pydantic'):
    assert not any(item == name or item.startswith(name + '.') for item in sys.modules), name
assert all(hasattr(workspace, name) for name in workspace.__all__)
assert all(hasattr(issue, name) for name in issue.__all__)
"""
    result = subprocess.run(
        [sys.executable, "-c", source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "name,enum",
    [
        (name, enum)
        for name, enum in vars(values).items()
        if name.startswith("Workspace") and get_origin(enum) is Literal
    ],
)
def test_every_finite_state_encodes_and_unknown_options_refuse(name, enum):
    record, field = next(
        (record, field)
        for record in values.PUBLICATION_VALUE_TYPES
        for field, annotation in get_type_hints(record).items()
        if annotation is enum
    )
    original = sample(record)
    for option in get_args(enum):
        value = dataclasses.replace(original, **{field: option})
        assert (
            codec.repository_publication_value_from_json(
                record, codec.repository_publication_value_to_json(value)
            )
            == value
        )
    with pytest.raises(codec.WorkspacePublicationValueError):
        codec.repository_publication_value_to_payload(
            dataclasses.replace(original, **{field: "unqualified"})
        )


def test_known_publication_survives_failed_cleanup_and_error_round_trip():
    effect = dataclasses.replace(
        sample(values.WorkspaceRepositoryPhysicalEffect), state="applied"
    )
    result = dataclasses.replace(
        sample(values.WorkspaceRepositoryCommitResult),
        publication_state="published",
        reference_update="cas_applied",
        index_projection="failed",
        cleanup_state="unknown",
        admission_completion="pending",
        ledger_complete=False,
        commit_hash="a" * 40,
        effects=(effect,),
        diagnostics=("physical cleanup incomplete",),
    )
    failure = dataclasses.replace(
        sample(values.WorkspaceRepositoryPublicationError),
        phase="cleanup",
        observation=result,
        result_validation_complete=False,
        original_cause_type="KeyboardInterrupt",
    )
    decoded = codec.repository_publication_value_from_json(
        type(failure), codec.repository_publication_value_to_json(failure)
    )
    assert decoded == failure
    assert decoded.observation.publication_state == "published"
    assert decoded.observation.commit_hash == "a" * 40
    assert decoded.observation.effects == (effect,)
    assert decoded.observation.cleanup_state == "unknown"


@pytest.mark.parametrize(
    "invalid", [None, [], {"device": 1}, {"device": 1, "inode": 2, "extra": 3}]
)
def test_nested_identity_shapes_refuse(invalid):
    payload = codec.repository_publication_value_to_payload(
        sample(values.WorkspaceRepositoryPhysicalEffect)
    )
    payload["before_identity"] = invalid
    if invalid is None:
        assert (
            codec.repository_publication_value_from_payload(
                values.WorkspaceRepositoryPhysicalEffect, payload
            ).before_identity
            is None
        )
    else:
        with pytest.raises(codec.WorkspacePublicationValueError):
            codec.repository_publication_value_from_payload(
                values.WorkspaceRepositoryPhysicalEffect, payload
            )


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        [None],
        [["git"]],
        [{"arguments": None}],
        [{"arguments": [True]}],
        [{"arguments": [], "extra": 1}],
    ],
)
def test_nested_command_shapes_refuse_without_mutation(invalid):
    payload = codec.repository_publication_value_to_payload(
        sample(values.WorkspaceRepositoryWriterObservation)
    )
    payload["command_log"] = invalid
    saved = json.dumps(payload)
    with pytest.raises(codec.WorkspacePublicationValueError):
        codec.repository_publication_value_from_payload(
            values.WorkspaceRepositoryWriterObservation, payload
        )
    assert json.dumps(payload) == saved
