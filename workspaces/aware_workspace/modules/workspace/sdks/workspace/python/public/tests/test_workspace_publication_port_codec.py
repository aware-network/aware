"""Production owner value/codec parity, not admission or writer qualification."""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import subprocess
import sys
import tomllib
import types
from functools import lru_cache
from pathlib import Path
from typing import Literal, get_args, get_origin, get_type_hints

import pytest
from aware_issue_sdk import repository_publication as issue
from aware_workspace_sdk import repository_publication as workspace
from aware_workspace_sdk.repository_publication import ports, values
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
OWNERS = {
    "workspace": ROOT
    / "workspaces/aware_workspace/modules/workspace/sdks/workspace/aware",
    "issue": ROOT / "workspaces/aware_coordination/modules/workflow/sdks/issue/aware",
}
FIXTURES = Path(__file__).parent / "fixtures"
CONTRACT = (
    ROOT / "docs/reports/workspace-publication-port-values-qualification-20261009.md"
)
RECORDS = ports.PUBLICATION_PORT_VALUE_TYPES + (
    issue.IssueRepositoryPublicationConsumeRequest,
    issue.IssueRepositoryFileIdentity,
    issue.IssueRepositoryPublicationPhysicalEffect,
    issue.IssueRepositoryPublicationLockReleaseObservation,
    issue.IssueRepositoryPublicationEffectObservation,
    issue.IssueRepositoryPublicationAdmissionObservation,
    issue.IssuePublicationCleanupObservation,
    issue.IssueCloseoutSourceObservation,
    issue.IssueCloseoutObservation,
)


def owner(record):
    return issue if record.__name__.startswith("Issue") else workspace


def sample(annotation, *, unknown=False):
    origin, arguments = get_origin(annotation), get_args(annotation)
    if origin is types.UnionType:
        return None if unknown else sample(arguments[0], unknown=unknown)
    if origin is Literal:
        return arguments[-1] if unknown else arguments[0]
    if annotation is str:
        return "évidence"
    if annotation is int:
        return 2**63 + 19
    if annotation is bool:
        return not unknown
    if annotation == tuple[int, int]:
        return (19, 29)
    if annotation == list[list[str]]:
        return [["git", "-C", "é x"], [], ["diff", "--", "a"]]
    if origin in (tuple, list):
        result = [sample(arguments[0], unknown=unknown)]
        return tuple(result) if origin is tuple else result
    hints = get_type_hints(annotation)
    return annotation(
        **{
            field.name: ("a", "é.txt")
            if field.name == "target_paths"
            else sample(hints[field.name], unknown=unknown)
            for field in dataclasses.fields(annotation)
        }
    )


@lru_cache
def lower(prefix):
    directory = OWNERS[prefix]
    manifest = tomllib.loads((directory / "aware.sdk.toml").read_text())["sdk"]
    paths = (
        "repository_publication_values.aware",
        "repository_publication_ports.aware",
    )
    documents = tuple(
        parse_neutral_aware_source(
            (directory / name).read_text(), source_path=f"/sdk/{prefix}/{name}"
        )
        for name in paths
    )
    return resolve_ontology_meaning(
        (
            OntologyMeaningPackageInput(
                package_name=manifest["package_name"],
                fqn_prefix=manifest["fqn_prefix"],
                sources_root=f"/sdk/{prefix}",
                dependencies=(),
                documents=documents,
                namespace_by_source_path=tuple(
                    (document.source_path, "") for document in documents
                ),
            ),
        ),
        selected_package_names=frozenset({manifest["package_name"]}),
    )


@pytest.mark.parametrize("record", RECORDS)
@pytest.mark.parametrize("unknown", [False, True])
def test_all_thirteen_values_round_trip_exactly_without_mutating_inputs(
    record, unknown
):
    api = owner(record)
    original = sample(record, unknown=unknown)
    payload = api.repository_publication_value_to_payload(original)
    before = json.dumps(payload, ensure_ascii=False)
    decoded = api.repository_publication_value_from_payload(record, payload)
    assert decoded == original and type(decoded) is record
    assert (
        api.repository_publication_value_from_json(
            record, api.repository_publication_value_to_json(original)
        )
        == original
    )
    assert json.dumps(payload, ensure_ascii=False) == before


@pytest.mark.parametrize("record", RECORDS)
def test_every_required_field_and_unknown_field_refuses_without_mutation(record):
    api = owner(record)
    payload = api.repository_publication_value_to_payload(sample(record))
    for field in payload:
        invalid = dict(payload)
        del invalid[field]
        saved = json.dumps(invalid)
        error = (
            api.IssuePublicationValueError
            if api is issue
            else api.WorkspacePublicationValueError
        )
        with pytest.raises(error):
            api.repository_publication_value_from_payload(record, invalid)
        assert json.dumps(invalid) == saved
    with pytest.raises(error):
        api.repository_publication_value_from_payload(
            record, dict(payload, authorized=True)
        )


@pytest.mark.parametrize("record", RECORDS)
def test_python_fields_and_all_annotations_match_real_production_lowering(record):
    prefix = "issue" if owner(record) is issue else "workspace"
    meaning = lower(prefix)
    fqn = f"aware_{prefix}_sdk.{record.__name__}"
    members = {
        entry.fqn.rsplit(".", 1)[1]: meaning_value_to_json(entry.payload)
        for entry in meaning.entries
        if entry.kind == "member" and entry.fqn.rsplit(".", 1)[0] == fqn
    }
    hints = get_type_hints(record)
    assert set(members) == set(hints)
    for position, field in enumerate(dataclasses.fields(record)):
        annotation = hints[field.name]
        nullable = get_origin(annotation) is types.UnionType
        if nullable:
            annotation = next(
                item for item in get_args(annotation) if item is not type(None)
            )
        member = members[field.name]
        assert member["position"] == position and member["nullable"] is nullable
        spelling = member["type_expression"].removesuffix("?")
        if get_origin(annotation) is Literal:
            enum_entries = sorted(
                (
                    entry
                    for entry in meaning.entries
                    if entry.kind == "enum_option"
                    and entry.fqn.rsplit(".", 1)[0] == f"aware_{prefix}_sdk.{spelling}"
                ),
                key=lambda entry: meaning_value_to_json(entry.payload)["position"],
            )
            assert tuple(
                entry.fqn.rsplit(".", 1)[1] for entry in enum_entries
            ) == get_args(annotation)
        elif get_origin(annotation) is tuple:
            item = get_args(annotation)[0]
            assert spelling == (
                {str: "String"}.get(item, getattr(item, "__name__", "")) + "[]"
            )
        else:
            assert spelling == {str: "String", int: "Int", bool: "Bool"}.get(
                annotation, getattr(annotation, "__name__", "")
            )
    symbol = next(
        entry
        for entry in meaning.entries
        if entry.kind == "symbol" and entry.fqn == fqn
    )
    assert meaning_value_to_json(symbol.payload)["inline_value"] is True


@pytest.mark.parametrize("record", RECORDS)
def test_each_production_value_matches_the_accepted_signature_not_a_new_rail(record):
    source = (
        CONTRACT.read_text()
        .split("<!-- normative-port-values-start -->", 1)[1]
        .split("```python\n", 1)[1]
        .split("```", 1)[0]
    )
    declaration = next(
        node for node in ast.parse(source).body if node.name == record.__name__
    )
    fields = {node.target.id: node.annotation for node in declaration.body}
    assert tuple(fields) == tuple(field.name for field in dataclasses.fields(record))
    hints = get_type_hints(record)
    for name, annotation in fields.items():
        actual = hints[name]
        if (
            isinstance(annotation, ast.Subscript)
            and isinstance(annotation.value, ast.Name)
            and annotation.value.id == "Literal"
        ):
            assert get_origin(actual) is Literal
            assert get_args(actual) == tuple(
                option.value for option in annotation.slice.elts
            )
        else:
            expected = ast.unparse(annotation)
            actual_text = str(actual).replace("<class '", "").replace("'>", "")
            for module in (
                issue.__name__ + ".",
                ports.__name__ + ".",
                values.__name__ + ".",
                "typing.",
            ):
                actual_text = actual_text.replace(module, "")
            assert actual_text == expected


@pytest.mark.parametrize("prefix", OWNERS)
def test_production_sources_preserve_accepted_fixture_bodies_and_manifest_selection(
    prefix,
):
    directory = OWNERS[prefix]
    production = (directory / "repository_publication_ports.aware").read_text()
    fixture = (FIXTURES / f"{prefix}_publication_port_values.aware").read_text()
    assert production.split("\n", 2)[2] == fixture.split("\n", 2)[2]
    assert (
        "*.aware"
        in tomllib.loads((directory / "aware.sdk.toml").read_text())["build"][
            "include_paths"
        ]
    )
    expected = {
        hashlib.sha256((directory / name).read_bytes()).hexdigest()
        for name in (
            "repository_publication_values.aware",
            "repository_publication_ports.aware",
        )
    }
    assert {
        pin.source_sha256 for entry in lower(prefix).entries for pin in entry.provenance
    } == expected


@pytest.mark.parametrize("prefix", OWNERS)
def test_complete_owner_value_slice_has_stable_meaning_and_preserves_all_roots(prefix):
    first = lower(prefix)
    lower.cache_clear()
    second = lower(prefix)
    assert first.canonical_bytes() == second.canonical_bytes()
    assert hashlib.sha256(first.canonical_bytes()).hexdigest() == first.canonical_sha256
    records = (
        values.PUBLICATION_VALUE_TYPES + ports.PUBLICATION_PORT_VALUE_TYPES
        if prefix == "workspace"
        else tuple(
            getattr(issue, name)
            for name in issue.__all__
            if name.startswith("Issue") and name != "IssuePublicationValueError"
        )
    )
    assert len(records) == (19 if prefix == "workspace" else 12)
    symbols = {entry.fqn for entry in first.entries if entry.kind == "symbol"}
    assert all(f"aware_{prefix}_sdk.{record.__name__}" in symbols for record in records)
    assert len(first.entries) == (273 if prefix == "workspace" else 234)
    print(
        json.dumps(
            {
                "owner": prefix,
                "entry_count": len(first.entries),
                "meaning_sha256": first.canonical_sha256,
            },
            sort_keys=True,
        )
    )


ENUM_FIELDS = tuple(
    (record, field, annotation)
    for record in RECORDS
    for field, annotation in get_type_hints(record).items()
    if get_origin(annotation) is Literal
)


@pytest.mark.parametrize(("record", "field", "annotation"), ENUM_FIELDS)
def test_every_finite_state_round_trips_and_unqualified_options_refuse(
    record, field, annotation
):
    api = owner(record)
    original = sample(record)
    for option in get_args(annotation):
        value = dataclasses.replace(original, **{field: option})
        assert (
            api.repository_publication_value_from_json(
                record, api.repository_publication_value_to_json(value)
            )
            == value
        )
    error = (
        api.IssuePublicationValueError
        if api is issue
        else api.WorkspacePublicationValueError
    )
    with pytest.raises(error):
        api.repository_publication_value_to_payload(
            dataclasses.replace(original, **{field: "unqualified"})
        )


@pytest.mark.parametrize("record", RECORDS)
def test_duplicate_root_and_nested_fields_refuse_in_json(record):
    api = owner(record)
    payload = api.repository_publication_value_to_payload(sample(record))
    source = api.repository_publication_value_to_json(sample(record))
    field = next(iter(payload))
    duplicate = (
        source[:-1] + "," + json.dumps(field) + ":" + json.dumps(payload[field]) + "}"
    )
    error = (
        api.IssuePublicationValueError
        if api is issue
        else api.WorkspacePublicationValueError
    )
    with pytest.raises(error, match="duplicate"):
        api.repository_publication_value_from_json(record, duplicate)


@pytest.mark.parametrize("record", RECORDS)
@pytest.mark.parametrize("invalid", ["NaN", "Infinity", "-Infinity", "1e999", "1.25"])
def test_nonfinite_and_floating_json_refuse_before_root_or_summary_selection(
    record, invalid
):
    api = owner(record)
    error = (
        api.IssuePublicationValueError
        if api is issue
        else api.WorkspacePublicationValueError
    )
    with pytest.raises(error):
        api.repository_publication_value_from_json(
            record, '{"omitted":' + invalid + "}"
        )


@pytest.mark.parametrize("record", RECORDS)
def test_caller_wrapper_same_name_and_cross_owner_types_cannot_reconstruct_authority(
    record,
):
    api = owner(record)
    error = (
        api.IssuePublicationValueError
        if api is issue
        else api.WorkspacePublicationValueError
    )
    forged = type(record.__name__, (), {})
    with pytest.raises(error):
        api.repository_publication_value_from_payload(forged, {})
    with pytest.raises(error):
        api.repository_publication_value_to_payload(forged())
    foreign = workspace if api is issue else issue
    foreign_error = (
        foreign.WorkspacePublicationValueError
        if foreign is workspace
        else foreign.IssuePublicationValueError
    )
    with pytest.raises(foreign_error):
        foreign.repository_publication_value_from_payload(record, {})


def test_workspace_observation_and_reconciliation_preserve_original_writer_on_known_publication_failure():
    from aware_workspace_operator.models import WorkspaceCommitReport

    original = WorkspaceCommitReport(
        repo_root="/repo/é",
        status="failed",
        commit_hash="a" * 40,
        candidate_commit="a" * 40,
        reference_update="cas_applied",
        updated_reference="refs/heads/main",
        shared_index_projection="failed",
        shared_index_projection_error="projection debt",
        index_reconciliation_pending=True,
        transaction_mode="isolated_index_atomic_ref_v1",
        command_log=[["git", "diff", "--", "é x"], []],
    )
    retained = dataclasses.replace(
        sample(values.WorkspaceRepositoryCommitResult),
        publication_state="published",
        commit_hash=original.commit_hash,
        reference_update="cas_applied",
        cleanup_state="unknown",
        admission_completion="pending",
        ledger_complete=False,
        original_writer_report=values.WorkspaceRepositoryWriterObservation(
            **original.model_dump()
        ),
    )
    for record in (
        ports.WorkspaceRepositoryPublicationObservation,
        ports.WorkspaceRepositoryIndexReconcileResult,
    ):
        value = dataclasses.replace(sample(record), result=retained)
        decoded = workspace.repository_publication_value_from_json(
            record, workspace.repository_publication_value_to_json(value)
        )
        report = WorkspaceCommitReport(
            **dataclasses.asdict(decoded.result.original_writer_report)
        )
        assert report.model_dump(mode="json") == original.model_dump(mode="json")
        assert decoded.result.publication_state == "published"
        assert (
            decoded.result.cleanup_state == "unknown"
            and decoded.result.admission_completion == "pending"
        )
        assert (
            len(dataclasses.fields(type(decoded.result.original_writer_report))) == 32
        )


def test_workspace_nested_lists_are_detached_both_directions():
    value = sample(ports.WorkspaceRepositoryPublicationObservation)
    wire = workspace.repository_publication_value_to_payload(value)
    decoded = workspace.repository_publication_value_from_payload(type(value), wire)
    value.result.original_writer_report.command_log[0].append("caller mutation")
    wire["result"]["original_writer_report"]["command_log"][0]["arguments"].append(
        "wire mutation"
    )
    assert decoded.result.original_writer_report.command_log[0] == ["git", "-C", "é x"]
    assert (
        "caller mutation"
        not in wire["result"]["original_writer_report"]["command_log"][0]["arguments"]
    )
    wire["diagnostics"].append("changed")
    assert decoded.diagnostics == ("évidence",)


def test_unknown_reachability_memory_and_index_completion_are_not_defaulted():
    for record in (
        ports.WorkspaceRepositoryPublicationObservation,
        ports.WorkspaceRepositoryIndexReconcileResult,
    ):
        value = sample(record, unknown=True)
        decoded = workspace.repository_publication_value_from_json(
            record, workspace.repository_publication_value_to_json(value)
        )
        assert decoded.result is None and decoded.ledger_complete is False
        if record is ports.WorkspaceRepositoryPublicationObservation:
            assert decoded.receipt_state == decoded.reachability_state == "unknown"
            assert decoded.expected_binding_matches is None
        else:
            assert (
                decoded.reconciliation_state == "unknown"
                and decoded.lock_release is None
            )


@pytest.mark.parametrize(
    "paths",
    [("b", "a"), ("a", "a"), ("/a",), ("a/../b",), ("e\u0301/a",), ("a\u0080b",)],
)
def test_reconciliation_paths_refuse_noncanonical_spelling_in_both_directions(paths):
    value = dataclasses.replace(
        sample(ports.WorkspaceRepositoryIndexReconcileRequest), target_paths=paths
    )
    with pytest.raises(workspace.WorkspacePublicationValueError):
        workspace.repository_publication_value_to_payload(value)
    wire = workspace.repository_publication_value_to_payload(sample(type(value)))
    wire["target_paths"] = list(paths)
    with pytest.raises(workspace.WorkspacePublicationValueError):
        workspace.repository_publication_value_from_payload(type(value), wire)


@pytest.mark.parametrize("invalid", [0, 1, "true", []])
def test_nullable_reachability_match_is_strict_boolean_or_explicit_null(invalid):
    value = sample(ports.WorkspaceRepositoryPublicationObservation)
    wire = workspace.repository_publication_value_to_payload(value)
    wire["expected_binding_matches"] = invalid
    with pytest.raises(workspace.WorkspacePublicationValueError):
        workspace.repository_publication_value_from_payload(type(value), wire)
    wire["expected_binding_matches"] = None
    assert (
        workspace.repository_publication_value_from_payload(
            type(value), wire
        ).expected_binding_matches
        is None
    )


def test_all_public_exports_resolve_normally_without_domain_implementation_imports():
    script = """
import sys
import aware_workspace_sdk.repository_publication as workspace
import aware_workspace_sdk.repository_publication.ports as ports
import aware_issue_sdk.repository_publication as issue
for api in (workspace, issue):
    assert len(api.__all__) == len(set(api.__all__))
    assert all(hasattr(api, name) for name in api.__all__)
assert len(ports.PUBLICATION_PORT_VALUE_TYPES) == 4
assert issue.IssueRepositoryFileIdentity(1, 2).inode == 2
for name in ('aware_workspace_runtime', 'aware_workspace_operator', 'aware_issue_runtime',
             'aware_issue_operational_runtime', 'aware_issue_fs_adapter', 'aware_orm',
             'aware_workspace_service_api', 'aware_workspace_service_dto', 'pydantic'):
    assert not any(item == name or item.startswith(name + '.') for item in sys.modules), name
for api, names in ((workspace, ('WorkspaceRepositoryCommitPlan', 'WorkspacePublicationWorkAdmission', 'publish_repository_commit')),
                   (issue, ('IssueRepositoryPublicationAdmission', 'IssueRepositoryPublicationLease', 'IssueCloseAdmission', 'consume_repository_publication'))):
    assert not any(hasattr(api, name) for name in names)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
