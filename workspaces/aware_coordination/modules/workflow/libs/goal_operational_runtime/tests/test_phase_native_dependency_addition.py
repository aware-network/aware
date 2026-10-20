from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from aware_goal_operational_runtime import (
    GoalDependencyRelation,
    GoalLanePhase,
    GoalLanePhaseDefinitionV1,
    GoalLanePhaseGate,
    GoalLanePhaseState,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
    GoalPhaseExecutionAuthorityV1,
    GoalPhaseNativeDependencyAdditionError,
    GoalPhaseNativeDocumentV2,
    issue_goal_phase_native_dependency_addition_receipt,
    plan_goal_phase_native_dependency_addition,
)

GOAL = "goal/2026-09-29/native-dependency-addition-v0"
MOUNT = GoalPhaseCoordinate(GOAL, "agent-in-experience", "a2-mounted-product-acceptance")
FOUNDATION = GoalPhaseCoordinate(GOAL, "agent-in-experience", "a2-mf-resident-foundation")


def _gate(key: str) -> GoalLanePhaseGate:
    return GoalLanePhaseGate(
        gate_key=key,
        promise=f"{key} accepted independently.",
        gate_contract_ref=f"contract:{key}",
        evidence_schema_ref=f"evidence:{key}",
    )


def _document(*, reverse: bool = False) -> GoalPhaseNativeDocumentV2:
    prefix = b"# Compatibility Goal\n"
    mount = GoalLanePhaseDefinitionV1(
        coordinate=MOUNT, ordinal=6, title="A2-M", intent="Mount the Agent in Product.",
        gate=_gate("mount"),
    )
    foundation = GoalLanePhaseDefinitionV1(
        coordinate=FOUNDATION, ordinal=10, title="A2-MF",
        intent="Provide resident Agent authority.", gate=_gate("foundation"),
    )
    dependencies = (
        GoalPhaseDependency(
            owner_goal_tag=GOAL, dependency_key="foundation-requires-mount",
            dependent=FOUNDATION, prerequisite=MOUNT,
            required_gate_digest=mount.gate.gate_digest,
            relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
            reason="Reverse edge for cycle proof.",
        ),
    ) if reverse else ()
    return GoalPhaseNativeDocumentV2(
        goal_tag=GOAL,
        compatibility_projection_sha256="sha256:" + hashlib.sha256(prefix).hexdigest(),
        compatibility_projection_byte_count=len(prefix),
        definitions=(mount, foundation),
        operational_bundle=GoalPhaseContractBundleV1(phases=(), dependencies=dependencies),
        unresolved_dependencies=(),
        source_refs=("repository-path:docs/goals/test.md",),
        execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
            proposal_aggregate_ref=(
                "goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64
            ),
            coordinator_acceptance_ref=(
                "goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:"
                + "3" * 64
            ),
        ),
    )


def _edge(document: GoalPhaseNativeDocumentV2) -> GoalPhaseDependency:
    return GoalPhaseDependency(
        owner_goal_tag=GOAL,
        dependency_key="a2-mounted-requires-resident-foundation",
        dependent=MOUNT,
        prerequisite=FOUNDATION,
        required_gate_digest=document.definitions[1].gate.gate_digest,
        relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
        reason="Mount only after the resident foundation is accepted.",
        evidence_refs=("issue:agent-foundation-direction",),
    )


def test_add_one_edge_to_definition_only_dependent_preserves_carrier() -> None:
    before = _document()
    edge = _edge(before)
    plan = plan_goal_phase_native_dependency_addition(document=before, dependency=edge)
    after = plan.after_document
    assert after.operational_bundle.dependencies == (edge,)
    assert after.operational_bundle.phases == before.operational_bundle.phases
    assert after.definitions == before.definitions
    assert after.unresolved_dependencies == before.unresolved_dependencies
    assert after.execution_authority == before.execution_authority
    assert after.source_refs == before.source_refs
    assert after.compatibility_projection_sha256 == before.compatibility_projection_sha256
    receipt = issue_goal_phase_native_dependency_addition_receipt(
        plan=plan, repository_commit_ref="a" * 40,
        changed_path="docs/goals/test.md",
        publication_issue_path="docs/issues/test.md",
        publication_issue_blob_oid="b" * 40,
    )
    assert receipt.after_document_ref == after.document_ref
    assert receipt.repository_commit_receipt_ref == "repository-commit:" + "a" * 40


def test_reject_missing_stale_duplicate_and_cycle() -> None:
    before = _document()
    edge = _edge(before)
    with pytest.raises(GoalPhaseNativeDependencyAdditionError, match="Gate digest"):
        plan_goal_phase_native_dependency_addition(
            document=before, dependency=replace(edge, required_gate_digest="sha256:" + "0" * 64)
        )
    with pytest.raises(GoalPhaseNativeDependencyAdditionError, match="must be defined"):
        plan_goal_phase_native_dependency_addition(
            document=before,
            dependency=replace(edge, prerequisite=GoalPhaseCoordinate(GOAL, "other", "missing")),
        )
    after = plan_goal_phase_native_dependency_addition(
        document=before, dependency=edge
    ).after_document
    with pytest.raises(GoalPhaseNativeDependencyAdditionError, match="already exists"):
        plan_goal_phase_native_dependency_addition(document=after, dependency=edge)
    with pytest.raises(ValueError, match="cycle"):
        plan_goal_phase_native_dependency_addition(document=_document(reverse=True), dependency=edge)


def test_forged_plan_and_mutated_plan_refuse_receipt() -> None:
    before = _document()
    plan = plan_goal_phase_native_dependency_addition(document=before, dependency=_edge(before))
    with pytest.raises(GoalPhaseNativeDependencyAdditionError, match="semantic intent"):
        replace(plan, semantic_intent_ref="goal-phase-native-dependency-addition-intent:sha256:" + "f" * 64)
    object.__setattr__(plan, "after_document", before)
    with pytest.raises(GoalPhaseNativeDependencyAdditionError, match="postimage"):
        issue_goal_phase_native_dependency_addition_receipt(
            plan=plan, repository_commit_ref="a" * 40,
            changed_path="docs/goals/test.md",
            publication_issue_path="docs/issues/test.md",
            publication_issue_blob_oid="b" * 40,
        )


def test_withdrawn_dependent_cannot_gain_retroactive_prerequisite() -> None:
    before = _document()
    definition = before.definitions[0]
    withdrawn = GoalLanePhase(
        coordinate=definition.coordinate,
        title=definition.title or "A2-M",
        ordinal=definition.ordinal,
        intent=definition.intent or "Mount the Agent in Product.",
        state=GoalLanePhaseState.WITHDRAWN,
        gate=definition.gate,
    )
    document = replace(
        before,
        operational_bundle=GoalPhaseContractBundleV1(
            phases=(withdrawn,), dependencies=(),
        ),
    )
    with pytest.raises(GoalPhaseNativeDependencyAdditionError, match="withdrawn dependent"):
        plan_goal_phase_native_dependency_addition(
            document=document, dependency=_edge(document),
        )
