from __future__ import annotations
# pyright: reportMissingImports=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownParameterType=false
# pyright: reportUnknownArgumentType=false, reportArgumentType=false
# pyright: reportUnusedCallResult=false

import hashlib
import json
from dataclasses import replace

import pytest
from aware_goal_operational_runtime.phase_contracts import (
    GoalLanePhaseGate,
    GoalPhaseContractBundleV1,
)
from aware_goal_operational_runtime.phase_document import (
    GoalLanePhaseDefinitionV1,
    GoalPhaseExecutionAuthorityV1,
    GoalPhaseNativeDocumentV2,
)
from aware_goal_operational_runtime.phase_migrated_definition_qualification import (
    GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1,
)
from aware_goal_operational_runtime.phase_migrated_gate_evaluation import (
    EvidenceBundleV1,
    EvaluationResult,
)
from aware_goal_operational_runtime.phase_migrated_qualification import (
    GoalPhaseMigratedQualificationError,
    GoalPhaseMigratedQualificationReconciliationV1,
    decode_goal_phase_migrated_qualification_publication_receipt,
    decode_goal_phase_migrated_qualification_reconciliation,
    issue_goal_phase_migrated_qualification_publication_receipt,
    plan_goal_phase_migrated_qualification,
)

import test_phase_migrated_gate_evaluation as m14


def _authority():
    gate = GoalLanePhaseGate(
        gate_key="accepted",
        promise="Accept migrated R3.",
        gate_contract_ref="aware.goal.phase-gate.profile/legacy_text_v1",
        evidence_schema_ref="aware.goal.phase-gate-evidence/unavailable_v1",
        invariant_refs=("invariant:legacy-lifecycle-is-source-snapshot",),
    )
    definition = GoalLanePhaseDefinitionV1(
        coordinate=m14.COORDINATE,
        ordinal=3,
        gate=gate,
        title="R3 Environment",
        intent="Admit real Environment authority.",
    )
    dependency, dependent_authority = m14._dependency_authority(
        m14.DependencyState.SATISFIED
    )
    prerequisite = dependent_authority["prerequisite_phase"]
    prerequisite_definition = GoalLanePhaseDefinitionV1(
        coordinate=prerequisite.coordinate,
        ordinal=2,
        gate=prerequisite.gate,
        title=prerequisite.title,
        intent=prerequisite.intent,
    )
    compatibility = b"# ActorWorld\n"
    document = GoalPhaseNativeDocumentV2(
        goal_tag=m14.COORDINATE.goal_tag,
        compatibility_projection_sha256="sha256:" + hashlib.sha256(compatibility).hexdigest(),
        compatibility_projection_byte_count=len(compatibility),
        definitions=(prerequisite_definition, definition),
        operational_bundle=GoalPhaseContractBundleV1(
            phases=(), dependencies=(dependency,)
        ),
        unresolved_dependencies=(),
        source_refs=("repository:path:docs/goals/actorworld.md",),
        execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "2" * 64,
            proposal_aggregate_ref="goal-phase-native-operational-bootstrap-proposal:sha256:" + "3" * 64,
            coordinator_acceptance_ref="goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:" + "4" * 64,
        ),
    )
    m13_receipt = GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1(
        semantic_intent_ref="goal-phase-definition-qualification-intent:sha256:" + "5" * 64,
        before_document_ref="goal-phase-document:sha256:" + "6" * 64,
        after_document_ref=document.document_ref,
        before_definition_ref="goal-phase-definition:sha256:" + "7" * 64,
        after_definition_ref=definition.definition_ref,
        proposal_publication_authority_ref="goal-phase-definition-qualification-proposal-publication:sha256:" + "8" * 64,
        acceptance_publication_authority_ref="goal-phase-definition-qualification-acceptance-publication:sha256:" + "9" * 64,
        publication_issue_authority_ref="goal-definition-qualification-publication-issue:sha256:" + "a" * 64,
        repository_parent_ref="b" * 40,
        repository_commit_ref="c" * 40,
        repository_commit_receipt_ref="repository-commit:" + "c" * 40,
        changed_path="docs/goals/actorworld.md",
        reconciliation_disposition="clear",
    )
    original_proposal, original_acceptance, original_bundle = m14._values(
        implementation_gate_digest=gate.gate_digest
    )
    entries = {item.role: item for item in original_bundle.entries}
    definition_evidence = replace(
        entries["definition_qualification"],
        m13_publication_receipt_ref=m13_receipt.receipt_ref,
        after_document_ref=document.document_ref,
        after_definition_ref=definition.definition_ref,
    )
    implementation = replace(
        entries["implementation_publication"],
        definition_ref=definition.definition_ref,
        gate_digest=gate.gate_digest,
    )
    review = replace(
        entries["independent_acceptance"],
        definition_ref=definition.definition_ref,
        gate_digest=gate.gate_digest,
    )
    closeout = replace(
        entries["implementation_closeout"],
        independent_verdict_ref=review.evidence_ref,
    )
    bundle = EvidenceBundleV1(
        entries=tuple(
            sorted(
                (
                    definition_evidence,
                    implementation,
                    review,
                    closeout,
                    entries["dependency:i2-requires-acceptance"],
                ),
                key=lambda item: (item.role, item.role_key),
            )
        )
    )
    proposal = replace(
        original_proposal,
        document_ref=document.document_ref,
        definition_ref=definition.definition_ref,
        gate_digest=gate.gate_digest,
    )
    acceptance = replace(
        original_acceptance,
        proposal_ref=proposal.proposal_ref,
        evidence_bundle_ref=bundle.bundle_ref,
    )
    verified = m14._verify((proposal, acceptance, bundle))
    return document, m13_receipt, verified


def _plan():
    document, m13_receipt, verified = _authority()
    return plan_goal_phase_migrated_qualification(
        document=document,
        m13_receipt=m13_receipt,
        verified_m14=verified,
        issue_ref="docs/issues/r3-sync.md",
        admitted_at="2026-09-23T02:00:00Z",
        evaluated_at="2026-09-23T01:59:00Z",
    )


def test_one_accepted_phase_preserves_every_other_carrier_component() -> None:
    plan = _plan()
    assert plan.evaluation.result is EvaluationResult.SATISFIED
    assert len(plan.before_document.operational_bundle.phases) == 0
    assert plan.after_document.operational_bundle.phases == (plan.phase,)
    assert plan.after_document.definitions == plan.before_document.definitions
    assert plan.after_document.operational_bundle.dependencies == plan.before_document.operational_bundle.dependencies
    assert plan.after_document.source_refs == plan.before_document.source_refs
    assert plan.after_document.execution_authority == plan.before_document.execution_authority
    assert plan.phase.state.value == "accepted"
    assert plan.phase.work_associations[0].role.value == "acceptance"


def test_forged_plan_and_reused_phase_are_rejected() -> None:
    plan = _plan()
    with pytest.raises(GoalPhaseMigratedQualificationError, match="canonical"):
        _ = replace(plan, after_document=plan.before_document)
    with pytest.raises(GoalPhaseMigratedQualificationError, match="already operational"):
        _ = plan_goal_phase_migrated_qualification(
            document=plan.after_document,
            m13_receipt=plan.m13_receipt,
            verified_m14=plan.verified_m14,
            issue_ref=plan.issue_ref,
            admitted_at=plan.admitted_at,
            evaluated_at=plan.evaluated_at,
        )


def test_definition_and_sealed_evaluation_drift_refuse() -> None:
    document, m13_receipt, verified = _authority()
    wrong_m13 = replace(
        m13_receipt,
        after_definition_ref="goal-phase-definition:sha256:" + "0" * 64,
    )
    with pytest.raises(GoalPhaseMigratedQualificationError, match="definition"):
        _ = plan_goal_phase_migrated_qualification(
            document=document,
            m13_receipt=wrong_m13,
            verified_m14=verified,
            issue_ref="docs/issues/r3-sync.md",
            admitted_at="2026-09-23T02:00:00Z",
            evaluated_at="2026-09-23T01:59:00Z",
        )
    object.__setattr__(verified, "coordinator_current", False)
    with pytest.raises(ValueError, match="forged or mutated"):
        _ = plan_goal_phase_migrated_qualification(
            document=document,
            m13_receipt=m13_receipt,
            verified_m14=verified,
            issue_ref="docs/issues/r3-sync.md",
            admitted_at="2026-09-23T02:00:00Z",
            evaluated_at="2026-09-23T01:59:00Z",
        )


def test_mutation_after_plan_creation_cannot_issue_receipt() -> None:
    plan = _plan()
    object.__setattr__(plan, "after_document", plan.before_document)
    with pytest.raises(GoalPhaseMigratedQualificationError, match="canonical"):
        _ = issue_goal_phase_migrated_qualification_publication_receipt(
            plan=plan,
            publication_issue_authority_ref="goal-publication-issue:sha256:" + "1" * 64,
            repository_parent_ref="d" * 40,
            repository_commit_ref="e" * 40,
            changed_path="docs/goals/actorworld.md",
        )


def test_receipt_canonical_round_trip_and_tamper_refusal() -> None:
    plan = _plan()
    receipt = issue_goal_phase_migrated_qualification_publication_receipt(
        plan=plan,
        publication_issue_authority_ref="goal-publication-issue:sha256:" + "1" * 64,
        repository_parent_ref="d" * 40,
        repository_commit_ref="e" * 40,
        changed_path="docs/goals/actorworld.md",
    )
    payload = json.dumps(
        receipt.to_wire(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    assert decode_goal_phase_migrated_qualification_publication_receipt(payload) == receipt
    changed = dict(receipt.to_wire())
    changed["phase_digest"] = "sha256:" + "f" * 64
    with pytest.raises(GoalPhaseMigratedQualificationError, match="canonical"):
        decode_goal_phase_migrated_qualification_publication_receipt(
            json.dumps(changed, sort_keys=True, separators=(",", ":")).encode()
        )


def test_reconciliation_receipt_is_strict_and_retains_publication() -> None:
    plan = _plan()
    publication = issue_goal_phase_migrated_qualification_publication_receipt(
        plan=plan,
        publication_issue_authority_ref="goal-publication-issue:sha256:" + "1" * 64,
        repository_parent_ref="d" * 40,
        repository_commit_ref="e" * 40,
        changed_path="docs/goals/actorworld.md",
    )
    reconciliation = GoalPhaseMigratedQualificationReconciliationV1(
        publication_receipt=publication,
        authoritative_commit="e" * 40,
        authoritative_goal_sha256="sha256:" + "a" * 64,
        worktree_disposition="clear",
    )
    payload = json.dumps(
        reconciliation.to_wire(), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True,
    ).encode()
    assert decode_goal_phase_migrated_qualification_reconciliation(payload) == reconciliation
    required = GoalPhaseMigratedQualificationReconciliationV1(
        publication_receipt=publication,
        authoritative_commit="e" * 40,
        authoritative_goal_sha256="sha256:" + "a" * 64,
        worktree_disposition="required",
    )
    assert required.publication_receipt == publication
    changed = dict(reconciliation.to_wire())
    changed["index_current"] = 1
    with pytest.raises(GoalPhaseMigratedQualificationError, match="authority fields"):
        decode_goal_phase_migrated_qualification_reconciliation(
            json.dumps(changed, sort_keys=True, separators=(",", ":")).encode()
        )
    object.__setattr__(publication, "m14_evaluation_ref", "forged")
    with pytest.raises(GoalPhaseMigratedQualificationError, match="publication receipt changed"):
        _ = GoalPhaseMigratedQualificationReconciliationV1(
            publication_receipt=publication,
            authoritative_commit="e" * 40,
            authoritative_goal_sha256="sha256:" + "a" * 64,
            worktree_disposition="clear",
        )
