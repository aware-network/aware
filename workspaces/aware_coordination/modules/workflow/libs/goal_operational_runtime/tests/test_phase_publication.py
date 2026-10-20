from __future__ import annotations

import json
from dataclasses import replace

import pytest
from aware_goal_operational_runtime import (
    GoalLanePhase,
    GoalLanePhaseDefinitionV1,
    GoalLanePhaseGate,
    GoalLanePhaseGateObservation,
    GoalLanePhaseGateOutcome,
    GoalLanePhaseState,
    GoalLanePhaseWork,
    GoalLanePhaseWorkDisposition,
    GoalLanePhaseWorkRole,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
    GoalPhaseDigestCurrentness,
    GoalPhaseExecutionAuthorityV1,
    GoalPhaseMutationKind,
    GoalPhaseMutationPlanV1,
    GoalPhaseNativeDocumentV2,
    GoalPhaseProjectionCurrentness,
    GoalPhaseProjectionRelation,
    GoalPhaseProjectionRevisionV1,
    GoalPhasePublicationState,
    GoalPhasePublicationReceiptV1,
    GoalPhaseReplayDisposition,
    GoalPhaseWorkCurrentness,
    GoalDependencyRelation,
    apply_goal_phase_mutation_to_native_document,
    assess_goal_phase_publication_currentness,
    bind_goal_phase_publication,
    decode_goal_phase_publication_receipt,
    issue_goal_phase_publication_receipt,
    plan_goal_phase_acceptance,
    plan_goal_phase_same_gate_successor,
    reconcile_goal_phase_projection,
    verify_goal_phase_publication_transition,
)
from aware_goal_operational_runtime.identity import fingerprint


def _revision(commit: str = "git:before") -> GoalPhaseProjectionRevisionV1:
    return GoalPhaseProjectionRevisionV1(
        repository_ref="refs/heads/main",
        repository_commit=commit,
        phase_blob_oid=f"blob:{commit}",
        source_sha256="sha256:" + "1" * 64,
    )


def _phase(
    *,
    outcome: GoalLanePhaseGateOutcome = GoalLanePhaseGateOutcome.PENDING,
) -> GoalLanePhase:
    gate = GoalLanePhaseGate(
        gate_key="phase-gate",
        promise="Phase publication is exact.",
        gate_contract_ref="contract:phase-publication-v1",
        evidence_schema_ref="evidence:phase-publication-v1",
    )
    observation = GoalLanePhaseGateObservation(
        observation_ref=f"observation:{outcome.value}",
        gate_digest=gate.gate_digest,
        outcome=outcome,
        evaluator_ref="evaluator:test",
        evidence_refs=(
            ("evidence:test",)
            if outcome is GoalLanePhaseGateOutcome.SATISFIED
            else ()
        ),
        source_revision_refs=("git:before",),
        evaluated_at="2026-09-19T19:00:00Z",
        currentness_ref="currentness:test",
    )
    work = GoalLanePhaseWork(
        association_ref="phase-work:first",
        issue_ref="docs/issues/first.md",
        role=GoalLanePhaseWorkRole.IMPLEMENTATION,
        disposition=GoalLanePhaseWorkDisposition.CURRENT,
        admitted_at="2026-09-19T18:00:00Z",
        receipt_ref="phase-work-admission:first",
    )
    return GoalLanePhase(
        coordinate=GoalPhaseCoordinate(
            "goal/2026-09-19/test-v0", "runtime", "publication"
        ),
        title="Publication",
        ordinal=4,
        intent="Publish Phase semantics atomically.",
        state=GoalLanePhaseState.ACTIVE,
        gate=gate,
        gate_observations=(observation,),
        work_associations=(work,),
        pursuit_directive="Continue only exact Phase publication work.",
    )


def test_same_gate_successor_changes_only_work_binding() -> None:
    phase = _phase()
    before = bind_goal_phase_publication(phase, projection_revision=_revision())
    plan = plan_goal_phase_same_gate_successor(
        phase=phase,
        expected_binding=before,
        expected_current_issue_ref="docs/issues/first.md",
        successor_issue_ref="docs/issues/review.md",
        successor_role=GoalLanePhaseWorkRole.REVIEW,
        timestamp="2026-09-19T19:10:00Z",
        evidence_refs=("commit:first",),
    )
    after = bind_goal_phase_publication(
        plan.after,
        projection_revision=_revision("git:after"),
    )
    assert after.coordinate == before.coordinate
    assert after.direction_digest == before.direction_digest
    assert after.gate_digest == before.gate_digest
    assert after.work_association_digest != before.work_association_digest
    assert [item.disposition for item in plan.after.work_associations] == [
        GoalLanePhaseWorkDisposition.RETIRED,
        GoalLanePhaseWorkDisposition.CURRENT,
    ]
    assert [item.issue_ref for item in plan.after.work_associations] == [
        "docs/issues/first.md",
        "docs/issues/review.md",
    ]


def test_same_gate_successor_applies_inside_v2_carrier_without_graph_drift() -> None:
    phase = _phase()
    before = bind_goal_phase_publication(phase, projection_revision=_revision())
    plan = plan_goal_phase_same_gate_successor(
        phase=phase,
        expected_binding=before,
        expected_current_issue_ref="docs/issues/first.md",
        successor_issue_ref="docs/issues/review.md",
        successor_role=GoalLanePhaseWorkRole.REVIEW,
        timestamp="2026-09-19T19:10:00Z",
        evidence_refs=("commit:first",),
    )
    authority = GoalPhaseExecutionAuthorityV1(
        source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
        parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
        proposal_aggregate_ref=(
            "goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64
        ),
        coordinator_acceptance_ref=(
            "goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:"
            + "3" * 64
        ),
    )
    document = GoalPhaseNativeDocumentV2(
        goal_tag=phase.coordinate.goal_tag,
        compatibility_projection_sha256="sha256:" + "4" * 64,
        compatibility_projection_byte_count=42,
        definitions=(
            GoalLanePhaseDefinitionV1(
                coordinate=phase.coordinate,
                title=phase.title,
                ordinal=phase.ordinal,
                intent=phase.intent,
                gate=phase.gate,
            ),
        ),
        operational_bundle=GoalPhaseContractBundleV1(
            phases=(phase,), dependencies=()
        ),
        unresolved_dependencies=(),
        source_refs=("repository-commit:before",),
        execution_authority=authority,
    )
    advanced = apply_goal_phase_mutation_to_native_document(
        document=document, plan=plan
    )
    assert advanced.operational_bundle.phases == (plan.after,)
    assert advanced.definitions == document.definitions
    assert advanced.operational_bundle.dependencies == ()
    assert advanced.unresolved_dependencies == ()
    assert advanced.source_refs == document.source_refs
    assert advanced.execution_authority == authority

    advanced_preimage = replace(phase, pursuit_directive="advanced")
    advanced_document = replace(
        document,
        operational_bundle=GoalPhaseContractBundleV1(
            phases=(advanced_preimage,), dependencies=()
        ),
    )
    with pytest.raises(ValueError, match="preimage"):
        apply_goal_phase_mutation_to_native_document(
            document=advanced_document, plan=plan
        )


def test_publication_transition_verifier_rejects_redigested_semantic_drift() -> None:
    phase = _phase()
    before_binding = bind_goal_phase_publication(
        phase, projection_revision=_revision()
    )
    plan = plan_goal_phase_same_gate_successor(
        phase=phase,
        expected_binding=before_binding,
        expected_current_issue_ref="docs/issues/first.md",
        successor_issue_ref="docs/issues/review.md",
        successor_role=GoalLanePhaseWorkRole.REVIEW,
        timestamp="2026-09-19T19:10:00Z",
        evidence_refs=("commit:first",),
    )
    authority = GoalPhaseExecutionAuthorityV1(
        source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
        parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
        proposal_aggregate_ref=(
            "goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64
        ),
        coordinator_acceptance_ref=(
            "goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:"
            + "3" * 64
        ),
    )
    definition = GoalLanePhaseDefinitionV1(
        coordinate=phase.coordinate,
        title=phase.title,
        ordinal=phase.ordinal,
        intent=phase.intent,
        gate=phase.gate,
    )
    document = GoalPhaseNativeDocumentV2(
        goal_tag=phase.coordinate.goal_tag,
        compatibility_projection_sha256="sha256:" + "4" * 64,
        compatibility_projection_byte_count=42,
        definitions=(definition,),
        operational_bundle=GoalPhaseContractBundleV1((phase,), ()),
        unresolved_dependencies=(),
        source_refs=("repository-commit:before",),
        execution_authority=authority,
    )
    advanced = apply_goal_phase_mutation_to_native_document(
        document=document, plan=plan
    )
    publication = issue_goal_phase_publication_receipt(
        plan=plan,
        after_projection_revision=_revision("git:published"),
        repository_commit_receipt_ref="repository-commit:git:published",
        changed_path="goal.md",
    )
    verify_goal_phase_publication_transition(
        before_document=document,
        after_document=advanced,
        publication_receipt=publication,
    )

    forged_phase = replace(plan.after, pursuit_directive="Forged direction")
    forged_document = replace(
        advanced,
        operational_bundle=GoalPhaseContractBundleV1((forged_phase,), ()),
    )
    forged_after_binding = bind_goal_phase_publication(
        forged_phase,
        projection_revision=publication.after_binding.projection_revision,
    )
    forged_body = {
        "schema_id": publication.schema_id,
        "plan_ref": publication.plan_ref,
        "operation": publication.operation.value,
        "coordinate": {
            "goal_tag": publication.coordinate.goal_tag,
            "lane_key": publication.coordinate.lane_key,
            "phase_key": publication.coordinate.phase_key,
        },
        "before_binding": publication.before_binding.to_wire(),
        "after_binding": forged_after_binding.to_wire(),
        "repository_commit_receipt_ref": publication.repository_commit_receipt_ref,
        "changed_paths": list(publication.changed_paths),
    }
    forged_receipt = GoalPhasePublicationReceiptV1(
        plan_ref=publication.plan_ref,
        operation=publication.operation,
        coordinate=publication.coordinate,
        before_binding=publication.before_binding,
        after_binding=forged_after_binding,
        repository_commit_receipt_ref=publication.repository_commit_receipt_ref,
        changed_paths=publication.changed_paths,
        receipt_ref="goal-phase-publication:" + fingerprint(forged_body),
    )
    with pytest.raises(ValueError, match="direction"):
        verify_goal_phase_publication_transition(
            before_document=document,
            after_document=forged_document,
            publication_receipt=forged_receipt,
        )

    other_coordinate = GoalPhaseCoordinate(
        goal_tag=phase.coordinate.goal_tag,
        lane_key="other-lane",
        phase_key="other-phase",
    )
    other = replace(
        phase,
        coordinate=other_coordinate,
        title="Other Phase",
        work_associations=(),
    )
    other_definition = GoalLanePhaseDefinitionV1(
        coordinate=other.coordinate,
        title=other.title,
        ordinal=other.ordinal,
        intent=other.intent,
        gate=other.gate,
    )
    dependency = GoalPhaseDependency(
        owner_goal_tag=phase.coordinate.goal_tag,
        dependency_key="first-requires-other",
        dependent=phase.coordinate,
        prerequisite=other.coordinate,
        required_gate_digest=other.gate.gate_digest,
        relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
        reason="The first Phase requires the other Phase.",
    )
    graph_document = replace(
        document,
        definitions=(definition, other_definition),
        operational_bundle=GoalPhaseContractBundleV1(
            (phase, other), (dependency,)
        ),
    )
    graph_advanced = apply_goal_phase_mutation_to_native_document(
        document=graph_document, plan=plan
    )
    unrelated_changed = replace(
        graph_advanced,
        operational_bundle=GoalPhaseContractBundleV1(
            (plan.after, replace(other, pursuit_directive="Changed other Phase")),
            (dependency,),
        ),
    )
    with pytest.raises(ValueError, match="unrelated Phase"):
        verify_goal_phase_publication_transition(
            before_document=graph_document,
            after_document=unrelated_changed,
            publication_receipt=publication,
        )
    dependency_changed = replace(
        graph_advanced,
        operational_bundle=GoalPhaseContractBundleV1(
            (plan.after, other),
            (replace(dependency, reason="Changed dependency meaning."),),
        ),
    )
    with pytest.raises(ValueError, match="protected carrier authority"):
        verify_goal_phase_publication_transition(
            before_document=graph_document,
            after_document=dependency_changed,
            publication_receipt=publication,
        )


def test_same_gate_successor_refuses_gate_or_work_drift() -> None:
    phase = _phase()
    binding = bind_goal_phase_publication(phase, projection_revision=_revision())
    changed_gate = replace(
        phase,
        gate=replace(phase.gate, promise="A materially different promise."),
        gate_observations=(),
    )
    with pytest.raises(ValueError, match="direction is stale|Gate is stale"):
        _ = plan_goal_phase_same_gate_successor(
            phase=changed_gate,
            expected_binding=binding,
            expected_current_issue_ref="docs/issues/first.md",
            successor_issue_ref="docs/issues/review.md",
            successor_role=GoalLanePhaseWorkRole.REVIEW,
            timestamp="2026-09-19T19:10:00Z",
            evidence_refs=("commit:first",),
        )
    with pytest.raises(ValueError, match="publication evidence"):
        _ = plan_goal_phase_same_gate_successor(
            phase=phase,
            expected_binding=binding,
            expected_current_issue_ref="docs/issues/first.md",
            successor_issue_ref="docs/issues/review.md",
            successor_role=GoalLanePhaseWorkRole.REVIEW,
            timestamp="2026-09-19T19:10:00Z",
            evidence_refs=(),
        )
    changed_work = replace(
        phase,
        work_associations=(
            replace(phase.work_associations[0], receipt_ref="foreign:receipt"),
        ),
    )
    with pytest.raises(ValueError, match="work associations are stale"):
        _ = plan_goal_phase_same_gate_successor(
            phase=changed_work,
            expected_binding=binding,
            expected_current_issue_ref="docs/issues/first.md",
            successor_issue_ref="docs/issues/review.md",
            successor_role=GoalLanePhaseWorkRole.REVIEW,
            timestamp="2026-09-19T19:10:00Z",
            evidence_refs=("commit:first",),
        )


def test_currentness_replays_only_unrelated_projection_advance() -> None:
    phase = _phase()
    expected = bind_goal_phase_publication(phase, projection_revision=_revision())
    observed = bind_goal_phase_publication(
        phase, projection_revision=_revision("git:unrelated-head")
    )
    currentness = assess_goal_phase_publication_currentness(
        expected=expected,
        observed=observed,
        projection_relation=GoalPhaseProjectionRelation.ANCESTOR,
        expected_phase=phase,
        observed_phase=phase,
    )
    assert currentness.direction_currentness is GoalPhaseDigestCurrentness.CURRENT
    assert currentness.gate_currentness is GoalPhaseDigestCurrentness.CURRENT
    assert currentness.work_currentness is GoalPhaseWorkCurrentness.CURRENT
    assert (
        currentness.projection_currentness
        is GoalPhaseProjectionCurrentness.ADVANCED
    )
    assert currentness.replay_disposition is GoalPhaseReplayDisposition.REPLAYABLE

    plan = plan_goal_phase_same_gate_successor(
        phase=phase,
        expected_binding=expected,
        expected_current_issue_ref="docs/issues/first.md",
        successor_issue_ref="docs/issues/review.md",
        successor_role=GoalLanePhaseWorkRole.REVIEW,
        timestamp="2026-09-19T19:10:00Z",
        evidence_refs=("commit:first",),
    )
    advanced = bind_goal_phase_publication(
        plan.after, projection_revision=_revision("git:work-advanced")
    )
    refused = assess_goal_phase_publication_currentness(
        expected=expected,
        observed=advanced,
        projection_relation=GoalPhaseProjectionRelation.ANCESTOR,
        expected_phase=phase,
        observed_phase=plan.after,
    )
    assert refused.work_currentness is GoalPhaseWorkCurrentness.ADVANCED
    assert refused.replay_disposition is GoalPhaseReplayDisposition.REFUSE

    detached = replace(phase, title="Detached title")
    with pytest.raises(ValueError, match="direction is stale"):
        _ = assess_goal_phase_publication_currentness(
            expected=expected,
            observed=observed,
            projection_relation=GoalPhaseProjectionRelation.ANCESTOR,
            expected_phase=detached,
            observed_phase=phase,
        )


def test_public_plan_and_receipt_refuse_forged_transition() -> None:
    phase = _phase()
    binding = bind_goal_phase_publication(phase, projection_revision=_revision())
    valid = plan_goal_phase_same_gate_successor(
        phase=phase,
        expected_binding=binding,
        expected_current_issue_ref="docs/issues/first.md",
        successor_issue_ref="docs/issues/review.md",
        successor_role=GoalLanePhaseWorkRole.REVIEW,
        timestamp="2026-09-19T19:10:00Z",
        evidence_refs=("commit:first",),
    )
    forged_after = replace(
        valid.after,
        gate=replace(valid.after.gate, promise="A forged Gate."),
        gate_observations=(),
    )
    with pytest.raises(ValueError, match="only work associations"):
        _ = GoalPhaseMutationPlanV1(
            operation=GoalPhaseMutationKind.CONTINUE_WORK,
            before=valid.before,
            after=forged_after,
            expected_binding=valid.expected_binding,
            evidence_refs=valid.evidence_refs,
            semantic_intent_ref=valid.semantic_intent_ref,
        )

    object.__setattr__(valid, "after", forged_after)
    with pytest.raises(ValueError, match="only work associations"):
        _ = issue_goal_phase_publication_receipt(
            plan=valid,
            after_projection_revision=_revision("git:forged"),
            repository_commit_receipt_ref="repository-commit-receipt:forged",
            changed_path="goal-phase.json",
        )


def test_public_plan_and_receipt_refuse_forged_work_admission_refs() -> None:
    phase = _phase()
    binding = bind_goal_phase_publication(phase, projection_revision=_revision())
    valid = plan_goal_phase_same_gate_successor(
        phase=phase,
        expected_binding=binding,
        expected_current_issue_ref="docs/issues/first.md",
        successor_issue_ref="docs/issues/review.md",
        successor_role=GoalLanePhaseWorkRole.REVIEW,
        timestamp="2026-09-19T19:10:00Z",
        evidence_refs=("commit:first",),
    )
    forged_successor = replace(
        valid.after.work_associations[-1],
        association_ref="forged:association",
        receipt_ref="forged:admission",
    )
    forged_after = replace(
        valid.after,
        work_associations=(
            *valid.after.work_associations[:-1],
            forged_successor,
        ),
    )
    forged_intent = "goal-phase-intent:" + fingerprint(
        {
            "schema_id": valid.schema_id,
            "operation": valid.operation.value,
            "expected_binding": valid.expected_binding.to_wire(),
            "expected_current_issue_ref": "docs/issues/first.md",
            "successor": {
                "association_ref": forged_successor.association_ref,
                "issue_ref": forged_successor.issue_ref,
                "role": forged_successor.role.value,
                "disposition": forged_successor.disposition.value,
                "admitted_at": forged_successor.admitted_at,
                "retired_at": forged_successor.retired_at,
                "receipt_ref": forged_successor.receipt_ref,
            },
            "evidence_refs": list(valid.evidence_refs),
        }
    )
    with pytest.raises(ValueError, match="successor is not canonical"):
        _ = GoalPhaseMutationPlanV1(
            operation=valid.operation,
            before=valid.before,
            after=forged_after,
            expected_binding=valid.expected_binding,
            evidence_refs=valid.evidence_refs,
            semantic_intent_ref=forged_intent,
        )

    object.__setattr__(valid, "after", forged_after)
    object.__setattr__(valid, "semantic_intent_ref", forged_intent)
    with pytest.raises(ValueError, match="successor is not canonical"):
        _ = issue_goal_phase_publication_receipt(
            plan=valid,
            after_projection_revision=_revision("git:forged-work"),
            repository_commit_receipt_ref="repository-commit-receipt:forged",
            changed_path="goal-phase.json",
        )


def test_acceptance_requires_satisfied_exact_gate_observation() -> None:
    pending = _phase()
    pending_binding = bind_goal_phase_publication(
        pending, projection_revision=_revision()
    )
    with pytest.raises(ValueError, match="satisfied current-Gate"):
        _ = plan_goal_phase_acceptance(
            phase=pending,
            expected_binding=pending_binding,
            gate_observation_ref="observation:pending",
            evidence_refs=("review:accepted",),
        )

    satisfied = _phase(outcome=GoalLanePhaseGateOutcome.SATISFIED)
    binding = bind_goal_phase_publication(satisfied, projection_revision=_revision())
    plan = plan_goal_phase_acceptance(
        phase=satisfied,
        expected_binding=binding,
        gate_observation_ref="observation:satisfied",
        evidence_refs=("review:accepted",),
    )
    assert plan.after.state is GoalLanePhaseState.ACCEPTED
    assert plan.acceptance_receipt_ref is not None
    assert plan.acceptance_receipt_ref.startswith("goal-phase-acceptance:sha256:")
    assert plan.after.last_receipt_ref == plan.acceptance_receipt_ref
    assert plan.after.gate == satisfied.gate
    assert plan.after.work_associations == satisfied.work_associations


def test_reconciliation_preserves_successful_publication_receipt() -> None:
    phase = _phase()
    binding = bind_goal_phase_publication(phase, projection_revision=_revision())
    plan = plan_goal_phase_same_gate_successor(
        phase=phase,
        expected_binding=binding,
        expected_current_issue_ref="docs/issues/first.md",
        successor_issue_ref="docs/issues/review.md",
        successor_role=GoalLanePhaseWorkRole.REVIEW,
        timestamp="2026-09-19T19:10:00Z",
        evidence_refs=("commit:first",),
    )
    publication = issue_goal_phase_publication_receipt(
        plan=plan,
        after_projection_revision=_revision("git:published"),
        repository_commit_receipt_ref="repository-commit:git:published",
        changed_path="goal-phase.json",
    )
    reconciliation = reconcile_goal_phase_projection(
        publication_receipt=publication,
        worktree_current=False,
        index_current=True,
        reason_codes=("worktree_projection_advanced",),
    )
    assert (
        reconciliation.publication_state
        is GoalPhasePublicationState.RECONCILIATION_REQUIRED
    )
    assert reconciliation.publication_receipt is publication
    assert (
        reconciliation.to_wire()["publication_receipt"]
        == publication.to_wire()
    )


def test_phase_publication_receipt_decoder_is_strict_and_digest_bound() -> None:
    phase = _phase()
    binding = bind_goal_phase_publication(phase, projection_revision=_revision())
    plan = plan_goal_phase_same_gate_successor(
        phase=phase,
        expected_binding=binding,
        expected_current_issue_ref="docs/issues/first.md",
        successor_issue_ref="docs/issues/review.md",
        successor_role=GoalLanePhaseWorkRole.REVIEW,
        timestamp="2026-09-19T19:10:00Z",
        evidence_refs=("commit:first",),
    )
    publication = issue_goal_phase_publication_receipt(
        plan=plan,
        after_projection_revision=_revision("git:published"),
        repository_commit_receipt_ref="repository-commit:git:published",
        changed_path="goal-phase.json",
    )
    payload = json.dumps(publication.to_wire()).encode()
    assert decode_goal_phase_publication_receipt(payload) == publication

    forged = publication.to_wire()
    forged["receipt_ref"] = "goal-phase-publication:sha256:" + "0" * 64
    with pytest.raises(ValueError, match="digest is invalid"):
        _ = decode_goal_phase_publication_receipt(json.dumps(forged).encode())

    wrong_commit = publication.to_wire()
    wrong_commit["repository_commit_receipt_ref"] = "repository-commit:other"
    with pytest.raises(ValueError, match="after projection commit"):
        _ = decode_goal_phase_publication_receipt(json.dumps(wrong_commit).encode())

    unknown = publication.to_wire()
    unknown["unknown"] = "field"
    with pytest.raises(ValueError, match="fields are noncanonical"):
        _ = decode_goal_phase_publication_receipt(json.dumps(unknown).encode())
