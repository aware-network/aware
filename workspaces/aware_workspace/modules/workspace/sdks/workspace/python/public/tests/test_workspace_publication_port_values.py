"""Remaining port shape qualification; no authority, provider or writer replay.

Unregistered fixtures lower through the genuine parser/resolver alongside the
unchanged production values. Documentation signatures are inspected as AST,
never executed as substitute owner implementations or capability constructors.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import get_args, get_type_hints

import pytest
from aware_issue_sdk import repository_publication as issue_values
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
REPORT = (
    ROOT / "docs/reports/workspace-publication-port-values-qualification-20261009.md"
)
BASE_CONTRACT = (
    ROOT / "docs/reports/workspace-publication-sdk-contract-freeze-20261009.md"
)
FIXTURES = Path(__file__).parent / "fixtures"
OWNERS = {
    "workspace": ROOT
    / "workspaces/aware_workspace/modules/workspace/sdks/workspace/aware",
    "issue": ROOT / "workspaces/aware_coordination/modules/workflow/sdks/issue/aware",
}
PORT_ROOTS = (
    "WorkspaceRepositoryPublicationObserveRequest",
    "WorkspaceRepositoryPublicationObservation",
    "WorkspaceRepositoryIndexReconcileRequest",
    "WorkspaceRepositoryIndexReconcileResult",
    "IssueRepositoryPublicationConsumeRequest",
    "IssueRepositoryPublicationEffectObservation",
    "IssueRepositoryPublicationAdmissionObservation",
    "IssuePublicationCleanupObservation",
    "IssueCloseoutSourceObservation",
    "IssueCloseoutObservation",
)
HELPERS = (
    "IssueRepositoryFileIdentity",
    "IssueRepositoryPublicationPhysicalEffect",
    "IssueRepositoryPublicationLockReleaseObservation",
)
OPAQUE = {
    "WorkspaceRepositoryCommitPlan",
    "WorkspacePublicationCapture",
    "WorkspacePublicationWorkAdmission",
    "WorkspacePublicationExecutionClaim",
    "WorkspacePublicationPhysicalTransaction",
    "IssueRepositoryPublicationAdmission",
    "IssueRepositoryPublicationEnrollment",
    "IssueRepositoryPublicationLease",
    "IssueCloseAdmission",
}
PREDECESSOR_PINS = {
    "workspaces/aware_workspace/modules/workspace/sdks/workspace/aware/repository_publication_values.aware": "ba07600c5b007ba99c49b78da7ba46cccde595fdd9e458d332453269287d6a7b",
    "workspaces/aware_coordination/modules/workflow/sdks/issue/aware/repository_publication_values.aware": "77532de598995c5f79ed8ec9ebf1ab6ceef316b226c1c8e6aa31f484df66d033",
    "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_publication/__init__.py": "949d35af6d150a01b3284ad6f86d1648df4075a26f0148f2522ca508d05a652a",
    "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_publication/values.py": "4fc0bb1528e70ceaa4092a19b0fa01135d1abec2383d9d226e4d82f895d729a7",
    "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_publication/codec.py": "f32f1a3871a0d9d593b7e0faaf37428cc799b677e5530bb2d8a2f777d53cef5a",
    "workspaces/aware_coordination/modules/workflow/sdks/issue/python/aware_issue_sdk/repository_publication.py": "5ada7f054f08ae633840585bbc13771be52ce3d3f16880c0aa8e8b4417a9b35f",
    "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_workspace_repository_publication_value_codec.py": "137c00c6d117b85fe2acfaedcdda74c1a4e1d3b3a869acd4e74adfc2b6748f1a",
    "workspaces/aware_coordination/modules/workflow/sdks/issue/python/tests/test_issue_repository_publication_value_codec.py": "1612a0ccbfc73b02b39c77ea225ed3b79b1136253cf81e15686718d43fd540ea",
}


def _tree():
    body = REPORT.read_text().split("<!-- normative-port-values-start -->", 1)[1]
    body = body.split("<!-- normative-port-values-end -->", 1)[0]
    return ast.parse(body.split("```python\n", 1)[1].split("```", 1)[0])


def _fields(name):
    node = next(node for node in _tree().body if node.name == name)
    assert isinstance(node, ast.ClassDef)
    assert all(
        isinstance(field, ast.AnnAssign) and field.value is None for field in node.body
    )
    return {field.target.id: field.annotation for field in node.body}


def _spelling(annotation, owner, field):
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        assert (
            isinstance(annotation.right, ast.Constant)
            and annotation.right.value is None
        )
        return _spelling(annotation.left, owner, field) + "?"
    if isinstance(annotation, ast.Name):
        return {"str": "String", "int": "Int", "bool": "Bool"}.get(
            annotation.id, annotation.id
        )
    assert isinstance(annotation, ast.Subscript) and isinstance(
        annotation.value, ast.Name
    )
    if annotation.value.id == "Literal":
        return owner + "".join(part.title() for part in field.split("_"))
    assert annotation.value.id == "tuple" and isinstance(annotation.slice, ast.Tuple)
    assert (
        isinstance(annotation.slice.elts[1], ast.Constant)
        and annotation.slice.elts[1].value is Ellipsis
    )
    return _spelling(annotation.slice.elts[0], owner, field) + "[]"


def _options(annotation):
    return tuple(item.value for item in annotation.slice.elts)


def _lower(prefix, source=None):
    manifest = tomllib.loads((OWNERS[prefix] / "aware.sdk.toml").read_text())["sdk"]
    sources = {
        "predecessor.aware": (
            OWNERS[prefix] / "repository_publication_values.aware"
        ).read_text(),
        "ports.aware": (
            FIXTURES / f"{prefix}_publication_port_values.aware"
        ).read_text()
        if source is None
        else source,
    }
    documents = tuple(
        parse_neutral_aware_source(body, source_path=f"/qualification/{prefix}/{name}")
        for name, body in sources.items()
    )
    return resolve_ontology_meaning(
        (
            OntologyMeaningPackageInput(
                package_name=manifest["package_name"],
                fqn_prefix=manifest["fqn_prefix"],
                sources_root=f"/qualification/{prefix}",
                dependencies=(),
                documents=documents,
                namespace_by_source_path=tuple(
                    (document.source_path, "") for document in documents
                ),
            ),
        ),
        selected_package_names=frozenset({manifest["package_name"]}),
    )


@lru_cache
def _meaning(prefix):
    return _lower(prefix)


def _members(name, meaning=None):
    prefix = "issue" if name.startswith("Issue") else "workspace"
    meaning = _meaning(prefix) if meaning is None else meaning
    return {
        entry.fqn.rsplit(".", 1)[1]: meaning_value_to_json(entry.payload)
        for entry in meaning.entries
        if entry.kind == "member"
        and entry.fqn.rsplit(".", 1)[0] == f"aware_{prefix}_sdk.{name}"
    }


def _assert_parity(name, meaning=None):
    members = _members(name, meaning)
    fields = _fields(name)
    assert set(members) == set(fields)
    for position, (field, annotation) in enumerate(fields.items()):
        spelling = _spelling(annotation, name, field)
        member = members[field]
        assert member["position"] == position
        assert member["type_expression"] == spelling
        assert member["nullable"] is spelling.endswith("?")
        assert member["collection"] is spelling.removesuffix("?").endswith("[]")
        assert member["identity_key"] is False
        if not member["primitive"]:
            assert member["target_fqn"] is not None
            assert member["target_symbol_kind"] in {"class_def", "enum_def"}


@pytest.mark.parametrize("name", PORT_ROOTS + HELPERS)
def test_exact_owned_fields_order_types_and_nullability_lower(name):
    _assert_parity(name)
    prefix = "issue" if name.startswith("Issue") else "workspace"
    symbol = next(
        entry
        for entry in _meaning(prefix).entries
        if entry.kind == "symbol" and entry.fqn == f"aware_{prefix}_sdk.{name}"
    )
    assert meaning_value_to_json(symbol.payload)["inline_value"] is True


ENUM_FIELDS = tuple(
    (name, field)
    for name in PORT_ROOTS + HELPERS
    for field, annotation in _fields(name).items()
    if isinstance(annotation, ast.Subscript)
    and isinstance(annotation.value, ast.Name)
    and annotation.value.id == "Literal"
)


@pytest.mark.parametrize(("name", "field"), ENUM_FIELDS)
def test_all_enum_options_preserve_exact_order(name, field):
    prefix = "issue" if name.startswith("Issue") else "workspace"
    enum = _spelling(_fields(name)[field], name, field)
    entries = sorted(
        (
            entry
            for entry in _meaning(prefix).entries
            if entry.kind == "enum_option"
            and entry.fqn.rsplit(".", 1)[0] == f"aware_{prefix}_sdk.{enum}"
        ),
        key=lambda entry: meaning_value_to_json(entry.payload)["position"],
    )
    assert tuple(entry.fqn.rsplit(".", 1)[1] for entry in entries) == _options(
        _fields(name)[field]
    )


@pytest.mark.parametrize("prefix", OWNERS)
def test_lowering_is_deterministic_with_exact_predecessor_and_fixture_provenance(
    prefix,
):
    first, second = _lower(prefix), _lower(prefix)
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.canonical_sha256 == second.canonical_sha256
    expected = {
        hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (
            OWNERS[prefix] / "repository_publication_values.aware",
            FIXTURES / f"{prefix}_publication_port_values.aware",
        )
    }
    assert {
        pin.source_sha256 for entry in first.entries for pin in entry.provenance
    } == expected
    assert all(entry.fqn.startswith(f"aware_{prefix}_sdk.") for entry in first.entries)


@pytest.mark.parametrize("name", PORT_ROOTS)
def test_new_values_cover_existing_frozen_port_references_without_new_ports(name):
    source = BASE_CONTRACT.read_text().split("<!-- normative-signatures-start -->", 1)[
        1
    ]
    tree = ast.parse(source.split("```python\n", 1)[1].split("```", 1)[0])
    assert any(
        isinstance(node, ast.Name) and node.id == name for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.ClassDef) and node.name == name for node in tree.body
    )


@pytest.mark.parametrize("path", PREDECESSOR_PINS)
def test_all_eight_accepted_production_source_pins_remain_unchanged(path):
    assert (
        hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == PREDECESSOR_PINS[path]
    )


@pytest.mark.parametrize("prefix", OWNERS)
def test_opaque_capabilities_and_authorization_bits_are_not_values(prefix):
    symbols = {
        entry.fqn.rsplit(".", 1)[1]
        for entry in _meaning(prefix).entries
        if entry.kind == "symbol"
    }
    assert not symbols & OPAQUE
    assert not symbols & {
        "IssueCloseRequest",
        "WorkspaceRepositoryPublicationClient",
        "IssueRepositoryPublicationClient",
    }
    for name in PORT_ROOTS + HELPERS:
        assert not set(_fields(name)) & {
            "authorized",
            "admitted",
            "may_write",
            "may_cleanup",
            "restore_authority",
        }


@pytest.mark.parametrize("name", PORT_ROOTS)
def test_current_codecs_refuse_new_shape_names_and_never_restore_authority(name):
    # Neither strings nor caller-built shape descriptors are recognized types.
    with pytest.raises(codec.WorkspacePublicationValueError):
        codec.repository_publication_value_from_payload(name, {})
    with pytest.raises(issue_values.IssuePublicationValueError):
        issue_values.repository_publication_value_from_payload(name, {})


def test_issue_effect_mirror_preserves_all_workspace_physical_fields_and_states():
    owner = values.WorkspaceRepositoryPhysicalEffect
    fields = _fields("IssueRepositoryPublicationPhysicalEffect")
    assert tuple(fields) == tuple(field.name for field in dataclasses.fields(owner))
    hints = get_type_hints(owner)
    assert _options(fields["kind"]) == get_args(hints["kind"])
    assert _options(fields["state"]) == get_args(hints["state"])
    for identity in ("before_identity", "after_identity"):
        assert ast.unparse(fields[identity]) == "IssueRepositoryFileIdentity | None"
    assert tuple(_fields("IssueRepositoryFileIdentity")) == ("device", "inode")
    assert all(
        ast.unparse(node) == "int"
        for node in _fields("IssueRepositoryFileIdentity").values()
    )


def test_issue_lock_mirror_preserves_all_workspace_release_fields_and_states():
    owner = values.WorkspaceRepositoryLockReleaseObservation
    fields = _fields("IssueRepositoryPublicationLockReleaseObservation")
    assert tuple(fields) == tuple(field.name for field in dataclasses.fields(owner))
    assert _options(fields["repository_lock_release"]) == get_args(
        get_type_hints(owner)["repository_lock_release"]
    )


@pytest.mark.parametrize(
    ("field", "annotation"),
    (
        ("publication_state", values.WorkspacePublicationState),
        ("reference_update", values.WorkspaceReferenceUpdateState),
        ("index_projection", values.WorkspaceIndexProjectionState),
        ("cleanup_state", values.WorkspaceCleanupState),
        (
            "admission_completion",
            values.WorkspaceRepositoryCommitResultAdmissionCompletion,
        ),
    ),
)
def test_issue_effect_finite_states_match_original_workspace_value_contract(
    field, annotation
):
    assert _options(
        _fields("IssueRepositoryPublicationEffectObservation")[field]
    ) == get_args(annotation)


def test_known_publication_failure_and_unknown_completion_have_distinct_carriers():
    fields = _fields("IssueRepositoryPublicationEffectObservation")
    assert _options(fields["publication_state"]) == (
        "not_published",
        "published",
        "unknown",
    )
    assert ast.unparse(fields["commit_hash"]) == "str | None"
    assert ast.unparse(fields["candidate_commit"]) == "str | None"
    assert ast.unparse(fields["index_reconciliation_pending"]) == "bool | None"
    assert (
        ast.unparse(fields["lock_release"])
        == "IssueRepositoryPublicationLockReleaseObservation | None"
    )
    assert _options(fields["admission_completion"]) == (
        "not_attempted",
        "completed",
        "pending",
        "unknown",
    )
    assert (
        ast.unparse(fields["effects"])
        == "tuple[IssueRepositoryPublicationPhysicalEffect, ...]"
    )
    assert ast.unparse(fields["workspace_observation_ref"]) == "str"
    assert ast.unparse(fields["binding"]) == "IssueRepositoryPublicationBinding"


def test_reachability_cannot_replace_original_provider_memory_or_admission():
    fields = _fields("WorkspaceRepositoryPublicationObservation")
    assert _options(fields["receipt_state"]) == ("present", "absent", "unknown")
    assert _options(fields["reachability_state"]) == (
        "reachable",
        "not_reachable",
        "unknown",
    )
    assert ast.unparse(fields["result"]) == "WorkspaceRepositoryCommitResult | None"
    assert ast.unparse(fields["expected_binding_matches"]) == "bool | None"
    assert (
        ast.unparse(fields["binding"]) == "WorkspaceRepositoryPublicationBinding | None"
    )
    assert "receipt_state" not in _fields(
        "IssueRepositoryPublicationAdmissionObservation"
    )


def test_reconciliation_preserves_full_original_writer_observation_and_debt():
    fields = _fields("WorkspaceRepositoryIndexReconcileResult")
    assert ast.unparse(fields["result"]) == "WorkspaceRepositoryCommitResult | None"
    assert (
        get_type_hints(values.WorkspaceRepositoryCommitResult)["original_writer_report"]
        == values.WorkspaceRepositoryWriterObservation | None
    )
    assert len(dataclasses.fields(values.WorkspaceRepositoryWriterObservation)) == 32
    assert _options(fields["reconciliation_state"]) == (
        "not_attempted",
        "applied",
        "pending",
        "failed",
        "unknown",
    )
    assert tuple(_fields("WorkspaceRepositoryIndexReconcileRequest")) == (
        "repository_ref",
        "publication_receipt_ref",
        "target_paths",
        "attempt_ref",
        "expected_head",
    )


def test_closeout_separates_source_cas_implementation_and_child_publication():
    source = _fields("IssueCloseoutSourceObservation")
    close = _fields("IssueCloseoutObservation")
    assert {
        "source_sha256_before",
        "source_sha256_after",
        "source_identity_before",
        "source_identity_after",
        "source_mode_before",
        "source_mode_after",
        "durability_confirmed",
    } <= set(source)
    assert ast.unparse(source["durability_confirmed"]) == "bool | None"
    assert _options(source["source_change_state"]) == (
        "not_attempted",
        "applied",
        "failed",
        "unknown",
    )
    assert ast.unparse(close["implementation_publication_receipt_ref"]) == "str"
    assert ast.unparse(close["closeout_publication_receipt_ref"]) == "str | None"
    assert (
        ast.unparse(close["publication_admission"])
        == "IssueRepositoryPublicationAdmissionObservation | None"
    )
    assert (
        ast.unparse(close["source_observation"])
        == "IssueCloseoutSourceObservation | None"
    )


def test_existing_close_request_is_consumed_at_its_original_sdk_constructor():
    from aware_issue_sdk.operation import IssueCloseRequest, IssueOperationContractError

    request = IssueCloseRequest(
        issue_ref="fb/2026-10-09/qualified",
        expected_source_sha256="sha256:" + "a" * 64,
        client_intent_id="attempt",
        actor_ref="execution",
        actor_evidence_ref="execution-proof",
        resolution="qualified",
        verified_by=("proof",),
        publication_receipt_ref="git:" + "b" * 40,
    )
    assert request.to_wire()["publication_receipt_ref"] == "git:" + "b" * 40
    assert request.to_wire()["verified_by"] == ["proof"]
    with pytest.raises(IssueOperationContractError):
        dataclasses.replace(request, verified_by=())
    assert "IssueCloseRequest" not in {node.name for node in _tree().body}


@pytest.mark.parametrize("prefix", OWNERS)
def test_undeclared_cross_owner_annotation_is_refused_by_real_resolver(prefix):
    source = (FIXTURES / f"{prefix}_publication_port_values.aware").read_text()
    source = (
        source.replace(
            "repository_ref String", "repository_ref UndeclaredForeignCapability", 1
        )
        if prefix == "workspace"
        else source.replace(
            "workspace_binding_ref String",
            "workspace_binding_ref UndeclaredForeignCapability",
            1,
        )
    )
    with pytest.raises(
        ValueError, match="UndeclaredForeignCapability.*does not resolve exactly once"
    ):
        _lower(prefix, source)


@pytest.mark.parametrize(
    ("name", "prefix", "before", "after"),
    (
        (
            "WorkspaceRepositoryPublicationObserveRequest",
            "workspace",
            "    expected_binding_ref String?\n",
            "",
        ),
        (
            "IssueCloseoutSourceObservation",
            "issue",
            "    source_sha256_after String?",
            "    source_sha256_after String",
        ),
        (
            "IssueRepositoryPublicationEffectObservation",
            "issue",
            "    effects IssueRepositoryPublicationPhysicalEffect[]",
            "    effects IssueRepositoryPublicationPhysicalEffect",
        ),
    ),
)
def test_field_nullability_and_collection_drift_cannot_pass_shape_parity(
    name, prefix, before, after
):
    source = (FIXTURES / f"{prefix}_publication_port_values.aware").read_text()
    assert before in source
    with pytest.raises(AssertionError):
        _assert_parity(name, _lower(prefix, source.replace(before, after, 1)))


def test_qualification_summary_is_reproducible_without_capture_or_authority():
    summary = {
        prefix: {
            "entry_count": len(_meaning(prefix).entries),
            "meaning_sha256": _meaning(prefix).canonical_sha256,
        }
        for prefix in OWNERS
    }
    assert json.loads(json.dumps(summary)) == summary
    assert {node.name for node in _tree().body} == set(PORT_ROOTS + HELPERS)
