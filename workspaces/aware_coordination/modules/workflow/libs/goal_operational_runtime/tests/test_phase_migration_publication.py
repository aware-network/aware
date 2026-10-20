from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from aware_goal_operational_runtime import (
    GoalPhaseMigrationPublicationError,
    issue_goal_phase_migration_publication_receipt,
    plan_goal_phase_native_migration_publication,
)


SOURCE = b"legacy-goal\n"
CANDIDATE = b"native-goal\n"
COMPATIBILITY = b"legacy-compatible-view\n"
GOAL_PATH = "docs/goals/example.md"
COORDINATOR_ACCEPTANCE = (
    "goal-phase-migration-aggregate-acceptance:sha256:" + "a" * 64
)
OPERATION_ACCEPTANCE = (
    "goal-phase-migration-operation-acceptance:sha256:" + "b" * 64
)


def _sha(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _aggregate(*, external_eligibility: str = "none") -> bytes:
    manifest = {
        "source": {
            "goal_doc_path": GOAL_PATH,
            "goal_tag": "goal/2026/09/20/example-v0",
            "goal_sha256": _sha(SOURCE),
            "repository_commit": "1" * 40,
            "authority_profile": "markdown_legacy_v1",
        },
        "authority_statement": {
            "current_goal_authority": "markdown_legacy_v1",
            "migration_row_authority": "legacy_governance_row_until_atomic_cut",
            "native_phase_authority": "not_admitted",
            "historical_pursuit_effect": "admission_evidence_only",
        },
        "lane_manifests": [
            {
                "lane_key": "lane-a",
                "manifest_path": "docs/reports/lane-a.json",
                "phase_count": 1,
                "canonical_manifest_byte_count": 10,
                "canonical_manifest_sha256": "sha256:" + "c" * 64,
                "owner_verdict_status": "optional_consultation",
                "publication_dependency": False,
            }
        ],
        "dependency_mappings": [
            {
                "dependency_key": "external",
                "required_prerequisite_gate_digest": None,
                "mapping_state": "external_gate_digest_unresolved",
                "operational_observation": None,
                "eligibility_effect": external_eligibility,
                "publication_disposition": (
                    "typed_unresolved_non_eligibility_producing"
                ),
            }
        ],
        "coordinator_acceptance": {
            "required": True,
            "authority": "actorworld_goal_governance_coordinator",
            "binding": "canonical_manifest_sha256",
            "receipt_location": "governance_issue_append_only_update",
        },
        "totals": {
            "lane_count": 1,
            "phase_mapping_count": 1,
            "dependency_mapping_count": 1,
            "pending_lane_owner_verdict_count": 0,
            "optional_lane_owner_consultation_count": 1,
            "external_unresolved_non_eligibility_dependency_count": 1,
        },
        "publication_preconditions": [
            "independent_coordinator_acceptance_of_aggregate_root",
            "independently_accepted_repository_cas_migration_effect",
            "fresh_whole_goal_recapture",
            "regenerated_aggregate_root_at_final_source_revision",
            "current_phase_profile_pursuit",
        ],
        "publication_candidate": {
            "goal_doc_path": GOAL_PATH,
            "before_goal_sha256": _sha(SOURCE),
            "after_goal_sha256": _sha(CANDIDATE),
            "compatibility_projection_sha256": _sha(COMPATIBILITY),
            "changed_paths": [GOAL_PATH],
            "phase_mapping_count": 1,
            "dependency_mapping_count": 1,
            "semantic_parity_ref": (
                "goal-phase-migration-parity:sha256:" + "d" * 64
            ),
            "current_phase_profile_pursuit_ref": (
                "goal-pursuit:sha256:" + "e" * 64
            ),
        },
    }
    canonical = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return (
        json.dumps(
            {
                "schema_id": "aware.goal.lane-phase-migration-aggregate.v1",
                "canonicalization": {
                    "profile": "sorted-keys-utf8-compact-json-v1",
                    "ensure_ascii": False,
                    "separators": [",", ":"],
                    "trailing_newline_in_digest": False,
                },
                "manifest": manifest,
                "canonical_manifest_byte_count": len(canonical),
                "canonical_manifest_sha256": _sha(canonical),
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode()


def _plan(
    aggregate: bytes | None = None,
    *,
    expected_aggregate_sha256: str | None = None,
):
    supplied = _aggregate() if aggregate is None else aggregate
    root = (
        json.loads(supplied)["canonical_manifest_sha256"]
        if expected_aggregate_sha256 is None
        else expected_aggregate_sha256
    )
    return plan_goal_phase_native_migration_publication(
        source_goal_bytes=SOURCE,
        candidate_goal_bytes=CANDIDATE,
        compatibility_projection_bytes=COMPATIBILITY,
        aggregate_bytes=supplied,
        expected_aggregate_sha256=root,
        coordinator_acceptance_ref=COORDINATOR_ACCEPTANCE,
        operation_acceptance_ref=OPERATION_ACCEPTANCE,
        idempotency_ref="example-migration-v1",
    )


def test_plans_exact_single_path_migration_and_issues_receipt() -> None:
    plan = _plan()
    assert plan.goal_doc_path == GOAL_PATH
    assert plan.phase_mapping_count == 1
    assert plan.dependency_mapping_count == 1
    assert plan.semantic_intent_ref.startswith(
        "goal-phase-migration-intent:sha256:"
    )
    receipt = issue_goal_phase_migration_publication_receipt(
        plan=plan,
        repository_commit_ref="f" * 40,
        repository_commit_receipt_ref="repository-commit:" + "f" * 40,
        publication_state="reconciliation_required",
        reconciliation_reason="worktree_projection_advanced",
    )
    assert receipt.receipt_ref.startswith(
        "goal-phase-migration-publication:sha256:"
    )
    with pytest.raises(GoalPhaseMigrationPublicationError, match="receipt_ref"):
        replace(receipt, receipt_ref="goal-phase-migration-publication:sha256:" + "0" * 64)
    with pytest.raises(GoalPhaseMigrationPublicationError, match="semantic_intent"):
        replace(plan, candidate_goal_sha256="sha256:" + "0" * 64)


def test_receipt_issuer_revalidates_mutated_public_plan() -> None:
    plan = _plan()
    object.__setattr__(plan, "candidate_goal_sha256", "sha256:" + "0" * 64)
    with pytest.raises(GoalPhaseMigrationPublicationError, match="semantic_intent"):
        issue_goal_phase_migration_publication_receipt(
            plan=plan,
            repository_commit_ref="f" * 40,
            repository_commit_receipt_ref="repository-commit:" + "f" * 40,
            publication_state="repository_published",
        )


def test_rejects_external_dependency_that_can_produce_eligibility() -> None:
    aggregate = _aggregate(external_eligibility="eligible")
    with pytest.raises(
        GoalPhaseMigrationPublicationError,
        match="unresolved dependency could produce eligibility",
    ):
        _plan(aggregate)


def test_rejects_candidate_and_aggregate_tampering() -> None:
    aggregate = json.loads(_aggregate())
    aggregate["manifest"]["publication_candidate"]["after_goal_sha256"] = _sha(
        b"different"
    )
    manifest = aggregate["manifest"]
    canonical = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    aggregate["canonical_manifest_byte_count"] = len(canonical)
    aggregate["canonical_manifest_sha256"] = _sha(canonical)
    payload = json.dumps(aggregate, sort_keys=True).encode()
    with pytest.raises(GoalPhaseMigrationPublicationError, match="candidate Goal"):
        _plan(payload)

    aggregate = json.loads(_aggregate())
    original_root = aggregate["canonical_manifest_sha256"]
    aggregate["canonical_manifest_byte_count"] += 1
    payload = json.dumps(aggregate, sort_keys=True).encode()
    with pytest.raises(GoalPhaseMigrationPublicationError, match="byte count"):
        _plan(payload, expected_aggregate_sha256=original_root)

    aggregate = json.loads(_aggregate())
    root = aggregate["canonical_manifest_sha256"]
    aggregate["canonicalization"]["ensure_ascii"] = 0
    with pytest.raises(
        GoalPhaseMigrationPublicationError,
        match="canonicalization",
    ):
        _plan(
            json.dumps(aggregate, sort_keys=True).encode(),
            expected_aggregate_sha256=root,
        )


def test_current_actorworld_aggregate_is_intentionally_not_publishable() -> None:
    path = Path(
        "docs/reports/actorworld-lane-phase-native-migration-20260920/aggregate.json"
    )
    if not path.is_file():
        pytest.skip("ActorWorld governance fixture is not present")
    aggregate = path.read_bytes()
    root = json.loads(aggregate)["canonical_manifest_sha256"]
    with pytest.raises(
        GoalPhaseMigrationPublicationError,
        match="manifest fields are not canonical",
    ):
        plan_goal_phase_native_migration_publication(
            source_goal_bytes=SOURCE,
            candidate_goal_bytes=CANDIDATE,
            compatibility_projection_bytes=COMPATIBILITY,
            aggregate_bytes=aggregate,
            expected_aggregate_sha256=root,
            coordinator_acceptance_ref=COORDINATOR_ACCEPTANCE,
            operation_acceptance_ref=OPERATION_ACCEPTANCE,
            idempotency_ref="must-remain-held",
        )
