from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from aware_goal_operational_runtime import (
    GoalDependencyRelation,
    GoalLanePhaseDefinitionV1,
    GoalLanePhaseGate,
    GoalLanePhaseWorkRole,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
    GoalPhaseExecutionAuthorityV1,
    GoalPhaseNativeAdmissionError,
    GoalPhaseNativeDocumentV1,
    GoalPhaseNativeDocumentV2,
    issue_goal_phase_native_admission_publication_receipt,
    plan_goal_phase_native_admission,
)

GOAL = "goal/2026-09-21/native-admission-test-v0"
EXTERNAL = "goal/2026-09-20/host-v0"


def _gate(key: str) -> GoalLanePhaseGate:
    return GoalLanePhaseGate(
        gate_key=key,
        promise=f"{key} is independently accepted.",
        gate_contract_ref=f"contract:{key}-v1",
        evidence_schema_ref=f"evidence:{key}-v1",
    )


def _document() -> GoalPhaseNativeDocumentV1:
    source = b"# Compatibility Goal\n"
    coordinate = GoalPhaseCoordinate(GOAL, "runtime", "m1")
    definition = GoalLanePhaseDefinitionV1(
        coordinate=coordinate,
        ordinal=1,
        gate=_gate("m1"),
        title="M1",
        intent="Establish the existing graph.",
    )
    return GoalPhaseNativeDocumentV1(
        goal_tag=GOAL,
        compatibility_projection_sha256="sha256:" + hashlib.sha256(source).hexdigest(),
        compatibility_projection_byte_count=len(source),
        definitions=(definition,),
        operational_bundle=GoalPhaseContractBundleV1(phases=(), dependencies=()),
        unresolved_dependencies=(),
        source_refs=("repository:path:docs/goals/test.md",),
    )


def _operational_document() -> GoalPhaseNativeDocumentV2:
    source = _document()
    return GoalPhaseNativeDocumentV2(
        goal_tag=source.goal_tag,
        compatibility_projection_sha256=source.compatibility_projection_sha256,
        compatibility_projection_byte_count=source.compatibility_projection_byte_count,
        definitions=source.definitions,
        operational_bundle=source.operational_bundle,
        unresolved_dependencies=source.unresolved_dependencies,
        source_refs=source.source_refs,
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


def _plan():
    coordinate = GoalPhaseCoordinate(GOAL, "native-ontology", "n1")
    prerequisite = GoalPhaseCoordinate(EXTERNAL, "runtime-host", "h5")
    gate = _gate("n1")
    dependency = GoalPhaseDependency(
        owner_goal_tag=GOAL,
        dependency_key="n1-requires-h5",
        dependent=coordinate,
        prerequisite=prerequisite,
        required_gate_digest="sha256:" + "5" * 64,
        relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
        reason="Consume only accepted H5 authority.",
        evidence_refs=("goal-phase-acceptance:sha256:" + "a" * 64,),
    )
    return plan_goal_phase_native_admission(
        document=_document(),
        coordinate=coordinate,
        ordinal=1,
        title="Phase-native Ontology consumer",
        intent=(
            "Persist the complete Phase-native graph without legacy G2 substitution."
        ),
        gate=gate,
        issue_ref="docs/issues/native-ontology.md",
        work_role=GoalLanePhaseWorkRole.IMPLEMENTATION,
        admitted_at="2026-09-21T01:00:00Z",
        work_evidence_refs=("issue-admission:native-ontology",),
        dependencies=(dependency,),
        evidence_refs=("issue-admission:native-ontology",),
        source_refs=("repository-commit:" + "b" * 40,),
    )


def test_plan_admits_exact_definition_phase_work_and_dependency() -> None:
    plan = _plan()
    assert len(plan.after_document.definitions) == 2
    assert plan.after_document.operational_bundle.phases == (plan.phase,)
    assert plan.after_document.operational_bundle.dependencies == plan.dependencies
    assert plan.phase.work_associations[0].issue_ref == "docs/issues/native-ontology.md"
    receipt = issue_goal_phase_native_admission_publication_receipt(
        plan=plan,
        repository_commit_ref="b" * 40,
        repository_commit_receipt_ref="repository-commit:" + "b" * 40,
        changed_path="docs/goals/test.md",
    )
    assert receipt.after_document_ref == plan.after_document.document_ref


def test_operational_v2_admission_preserves_existing_authority() -> None:
    baseline = _plan()
    source = _operational_document()
    plan = plan_goal_phase_native_admission(
        document=source,
        coordinate=baseline.phase.coordinate,
        ordinal=baseline.phase.ordinal,
        title=baseline.phase.title,
        intent=baseline.phase.intent,
        gate=baseline.phase.gate,
        issue_ref=baseline.phase.work_associations[0].issue_ref,
        work_role=baseline.phase.work_associations[0].role,
        admitted_at=baseline.phase.work_associations[0].admitted_at,
        work_evidence_refs=baseline.evidence_refs,
        dependencies=baseline.dependencies,
        evidence_refs=baseline.evidence_refs,
        source_refs=("repository-commit:" + "b" * 40,),
    )
    after = plan.after_document
    assert type(after) is GoalPhaseNativeDocumentV2
    assert after.execution_authority == source.execution_authority
    assert after.source_refs == source.source_refs
    assert after.definitions[:-1] == source.definitions
    assert after.operational_bundle.phases[:-1] == source.operational_bundle.phases
    assert after.operational_bundle.dependencies[:-1] == source.operational_bundle.dependencies
    assert after.unresolved_dependencies == source.unresolved_dependencies
    receipt = issue_goal_phase_native_admission_publication_receipt(
        plan=plan,
        repository_commit_ref="b" * 40,
        repository_commit_receipt_ref="repository-commit:" + "b" * 40,
        changed_path="docs/goals/test.md",
    )
    assert receipt.after_document_ref == after.document_ref
    with pytest.raises(GoalPhaseNativeAdmissionError, match="canonical"):
        issue_goal_phase_native_admission_publication_receipt(
            plan=replace(plan, source_refs=("repository-commit:" + "c" * 40,)),
            repository_commit_ref="b" * 40,
            repository_commit_receipt_ref="repository-commit:" + "b" * 40,
            changed_path="docs/goals/test.md",
        )
    with pytest.raises(GoalPhaseNativeAdmissionError, match="canonical"):
        issue_goal_phase_native_admission_publication_receipt(
            plan=replace(
                plan,
                after_document=replace(
                    after,
                    source_refs=tuple(sorted(after.source_refs + ("repository-commit:" + "c" * 40,))),
                ),
            ),
            repository_commit_ref="b" * 40,
            repository_commit_receipt_ref="repository-commit:" + "b" * 40,
            changed_path="docs/goals/test.md",
        )


def test_receipt_preserves_explicit_repeated_repository_path_source() -> None:
    existing_path = "repository-path:docs/goals/test.md"
    document = replace(_document(), source_refs=(existing_path,))
    baseline = _plan()
    plan = plan_goal_phase_native_admission(
        document=document,
        coordinate=baseline.phase.coordinate,
        ordinal=baseline.phase.ordinal,
        title=baseline.phase.title,
        intent=baseline.phase.intent,
        gate=baseline.phase.gate,
        issue_ref=baseline.phase.work_associations[0].issue_ref,
        work_role=baseline.phase.work_associations[0].role,
        admitted_at=baseline.phase.work_associations[0].admitted_at,
        work_evidence_refs=baseline.evidence_refs,
        dependencies=baseline.dependencies,
        evidence_refs=baseline.evidence_refs,
        source_refs=("repository-commit:" + "b" * 40, existing_path),
    )

    receipt = issue_goal_phase_native_admission_publication_receipt(
        plan=plan,
        repository_commit_ref="b" * 40,
        repository_commit_receipt_ref="repository-commit:" + "b" * 40,
        changed_path="docs/goals/test.md",
    )

    assert receipt.plan_ref == plan.semantic_intent_ref


def test_plan_allows_phase_without_incoming_dependencies() -> None:
    plan = _plan()
    independent = plan_goal_phase_native_admission(
        document=_document(),
        coordinate=GoalPhaseCoordinate(GOAL, "independent-runtime", "n1"),
        ordinal=1,
        title="Independent native Phase",
        intent="Admit work without manufacturing an incoming dependency.",
        gate=_gate("independent"),
        issue_ref="docs/issues/independent.md",
        work_role=GoalLanePhaseWorkRole.IMPLEMENTATION,
        admitted_at="2026-09-21T01:00:00Z",
        work_evidence_refs=("issue-admission:independent",),
        dependencies=(),
        evidence_refs=("issue-admission:independent",),
        source_refs=("repository-commit:" + "c" * 40,),
    )
    assert independent.dependencies == ()
    assert independent.after_document.operational_bundle.dependencies == ()


def test_existing_coordinate_and_noncanonical_dependencies_fail() -> None:
    plan = _plan()
    with pytest.raises(GoalPhaseNativeAdmissionError, match="already exists"):
        plan_goal_phase_native_admission(
            document=plan.after_document,
            coordinate=plan.phase.coordinate,
            ordinal=1,
            title=plan.phase.title,
            intent=plan.phase.intent,
            gate=plan.phase.gate,
            issue_ref="docs/issues/second.md",
            work_role=GoalLanePhaseWorkRole.IMPLEMENTATION,
            admitted_at="2026-09-21T02:00:00Z",
            work_evidence_refs=("evidence:second",),
            dependencies=(),
            evidence_refs=("evidence:second",),
            source_refs=("repository-commit:" + "c" * 40,),
        )
    with pytest.raises(GoalPhaseNativeAdmissionError, match="target the new Phase"):
        plan_goal_phase_native_admission(
            document=_document(),
            coordinate=plan.phase.coordinate,
            ordinal=1,
            title=plan.phase.title,
            intent=plan.phase.intent,
            gate=plan.phase.gate,
            issue_ref="docs/issues/native-ontology.md",
            work_role=GoalLanePhaseWorkRole.IMPLEMENTATION,
            admitted_at="2026-09-21T01:00:00Z",
            work_evidence_refs=("issue-admission:native-ontology",),
            dependencies=(
                replace(
                    plan.dependencies[0],
                    dependent=GoalPhaseCoordinate(GOAL, "other", "n1"),
                ),
            ),
            evidence_refs=("issue-admission:native-ontology",),
            source_refs=("repository-commit:" + "b" * 40,),
        )


def test_zero_ordinal_fails_before_repository_publication() -> None:
    plan = _plan()
    with pytest.raises(GoalPhaseNativeAdmissionError, match="positive integer"):
        plan_goal_phase_native_admission(
            document=_document(),
            coordinate=plan.phase.coordinate,
            ordinal=0,
            title=plan.phase.title,
            intent=plan.phase.intent,
            gate=plan.phase.gate,
            issue_ref="docs/issues/native-ontology.md",
            work_role=GoalLanePhaseWorkRole.IMPLEMENTATION,
            admitted_at="2026-09-21T01:00:00Z",
            work_evidence_refs=("issue-admission:native-ontology",),
            dependencies=plan.dependencies,
            evidence_refs=("issue-admission:native-ontology",),
            source_refs=("repository-commit:" + "b" * 40,),
        )


def test_forged_plan_fails_before_publication_receipt() -> None:
    plan = _plan()
    forged_phase = replace(
        plan.phase,
        work_associations=(
            replace(plan.phase.work_associations[0], receipt_ref="forged"),
        ),
    )
    forged = replace(plan, phase=forged_phase)
    with pytest.raises(GoalPhaseNativeAdmissionError, match="canonical"):
        issue_goal_phase_native_admission_publication_receipt(
            plan=forged,
            repository_commit_ref="b" * 40,
            repository_commit_receipt_ref="repository-commit:" + "b" * 40,
            changed_path="docs/goals/test.md",
        )
