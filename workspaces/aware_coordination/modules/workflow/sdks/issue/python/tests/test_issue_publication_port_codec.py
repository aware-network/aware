"""Issue-only successor refusal/evidence proofs; no Workspace provider import."""

from __future__ import annotations

import dataclasses
import json

import pytest
from aware_issue_sdk import repository_publication as values


def binding():
    return values.IssueRepositoryPublicationBinding(
        "binding",
        "attempt",
        "repository",
        "refs/heads/main",
        None,
        ("a",),
        "sha256:" + "a" * 64,
        "sha256:" + "b" * 64,
        "generation",
        "workspace-provider",
        "execution",
    )


def effect():
    return values.IssueRepositoryPublicationPhysicalEffect(
        "effect",
        "refs/heads/main",
        "repository_reference_update",
        "applied",
        "before",
        "after",
        "sha256:" + "a" * 64,
        "sha256:" + "b" * 64,
        values.IssueRepositoryFileIdentity(19, 29),
        values.IssueRepositoryFileIdentity(31, 37),
        0o600,
        None,
        ("durability unknown",),
    )


def publication():
    return values.IssueRepositoryPublicationEffectObservation(
        binding(),
        "workspace-observation",
        "spent-work-receipt",
        "git:" + "a" * 40,
        "published",
        "b" * 40,
        "a" * 40,
        "a" * 40,
        "refs/heads/main",
        "cas_applied",
        "failed",
        "unknown",
        None,
        "pending",
        "isolated_index_atomic_ref_v1",
        None,
        True,
        (effect(),),
        False,
        ("known publication; cleanup unavailable",),
    )


def source():
    return values.IssueCloseoutSourceObservation(
        "issue",
        "issue-provider",
        "generation",
        "execution",
        "source-observation",
        "attempt",
        "close-parent-receipt",
        "docs/issues/é.md",
        "applied",
        "sha256:" + "a" * 64,
        "sha256:" + "b" * 64,
        values.IssueRepositoryFileIdentity(19, 29),
        values.IssueRepositoryFileIdentity(31, 37),
        0o640,
        0o640,
        None,
        "unknown",
        False,
        ("source applied; durability unknown",),
    )


def test_known_publication_and_source_effect_survive_cleanup_and_closeout_serialization():
    observed = publication()
    admission = values.IssueRepositoryPublicationAdmissionObservation(
        "issue",
        "sha256:" + "c" * 64,
        "issue-provider",
        "generation",
        "execution",
        "admission-observation",
        "attempt",
        binding(),
        "admission-receipt",
        "enrollment-receipt",
        "spent-work-receipt",
        "consumer",
        "issue_closeout_publication",
        "spent",
        "consumed",
        "pending",
        observed,
        False,
        ("finish unavailable",),
    )
    closeout = values.IssueCloseoutObservation(
        "issue",
        "issue-provider",
        "generation",
        "execution",
        "close-observation",
        "attempt",
        "close-parent-receipt",
        "git:" + "d" * 40,
        "git:" + "a" * 40,
        source(),
        admission,
        "pending",
        False,
        ("completion unconfirmed",),
    )
    cleanup = values.IssuePublicationCleanupObservation(
        "issue",
        "issue-provider",
        "generation",
        "execution",
        "cleanup-observation",
        "attempt",
        "admission-receipt",
        "unknown",
        "unknown",
        observed,
        source(),
        False,
        ("cleanup unknown; do not retry from snapshot",),
    )
    for value in (closeout, cleanup):
        decoded = values.repository_publication_value_from_json(
            type(value), values.repository_publication_value_to_json(value)
        )
        assert decoded == value
        pub = (
            decoded.publication
            if type(value) is type(cleanup)
            else decoded.publication_admission.publication
        )
        assert pub.publication_state == "published" and pub.commit_hash == "a" * 40
        assert pub.cleanup_state == "unknown" and pub.admission_completion == "pending"
        assert pub.effects == (effect(),) and pub.binding == binding()
        assert decoded.source_observation.source_change_state == "applied"
        assert decoded.source_observation.durability_confirmed is None
    assert (
        closeout.implementation_publication_receipt_ref
        != closeout.closeout_publication_receipt_ref
    )


@pytest.mark.parametrize("field", ["effects", "binding", "lock_release"])
@pytest.mark.parametrize("invalid", [True, "wrong", [None], {"authorized": True}])
def test_nested_malformed_evidence_refuses_without_mutating_source(field, invalid):
    wire = values.repository_publication_value_to_payload(publication())
    wire[field] = invalid
    saved = json.dumps(wire)
    with pytest.raises(values.IssuePublicationValueError):
        values.repository_publication_value_from_payload(
            values.IssueRepositoryPublicationEffectObservation, wire
        )
    assert json.dumps(wire) == saved


@pytest.mark.parametrize("invalid", [True, 1.0, "1", None])
def test_issue_identity_ints_refuse_boolean_coercion_and_nulls(invalid):
    with pytest.raises(values.IssuePublicationValueError):
        values.repository_publication_value_from_payload(
            values.IssueRepositoryFileIdentity, {"device": invalid, "inode": 29}
        )


@pytest.mark.parametrize("invalid", [0, 1, "true", []])
def test_issue_boolean_observations_refuse_coercion(invalid):
    wire = values.repository_publication_value_to_payload(source())
    wire["ledger_complete"] = invalid
    with pytest.raises(values.IssuePublicationValueError):
        values.repository_publication_value_from_payload(
            values.IssueCloseoutSourceObservation, wire
        )


@pytest.mark.parametrize(
    "path",
    ["", "/a", "a\\b", ".", "..", "a/../b", "a//b", "a/", "e\u0301/a", "a\ud800"]
    + [f"a{chr(number)}b" for number in (*range(32), *range(127, 160))],
)
def test_closeout_source_coordinate_uses_the_same_exact_canonical_path_profile(path):
    value = dataclasses.replace(source(), source_path=path)
    with pytest.raises(values.IssuePublicationValueError):
        values.repository_publication_value_to_payload(value)
    wire = values.repository_publication_value_to_payload(source())
    wire["source_path"] = path
    with pytest.raises(values.IssuePublicationValueError):
        values.repository_publication_value_from_payload(type(value), wire)


def test_issue_nested_identity_and_effect_collections_are_detached():
    value = publication()
    wire = values.repository_publication_value_to_payload(value)
    decoded = values.repository_publication_value_from_payload(type(value), wire)
    wire["effects"][0]["before_identity"]["device"] = 999
    wire["effects"][0]["diagnostics"].append("changed")
    wire["effects"].clear()
    assert decoded.effects == (effect(),) and value.effects == decoded.effects


def test_nested_duplicate_fields_are_refused_without_hiding_known_publication():
    value = publication()
    source_json = values.repository_publication_value_to_json(value)
    duplicate = source_json.replace('"device":19', '"device":19,"device":19', 1)
    assert duplicate != source_json
    with pytest.raises(values.IssuePublicationValueError, match="duplicate"):
        values.repository_publication_value_from_json(type(value), duplicate)
    assert value.publication_state == "published" and value.effects == (effect(),)


def test_unknown_is_preserved_and_missing_evidence_is_not_defaulted():
    value = dataclasses.replace(
        publication(),
        publication_state="unknown",
        publication_receipt_ref=None,
        commit_hash=None,
        index_reconciliation_pending=None,
        effects=(),
        lock_release=None,
    )
    wire = values.repository_publication_value_to_payload(value)
    decoded = values.repository_publication_value_from_payload(type(value), wire)
    assert decoded == value and decoded.publication_state == "unknown"
    del wire["lock_release"]
    with pytest.raises(values.IssuePublicationValueError):
        values.repository_publication_value_from_payload(type(value), wire)
