from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from aware_goal_operational_runtime.phase_shared_operation import (
    validate_goal_phase_eligibility_decision_v2_wire,
)

from aware_goal_operational_runtime import (
    GoalDependencyRelation,
    GoalFrontierCurrentness,
    GoalGlobalDirectionAuthorityV1,
    GoalLaneDirectionAuthorityV1,
    GoalLanePhase,
    GoalLanePhaseDefinitionV1,
    GoalNativeLaneAuthorityV1,
    GoalLanePhaseGate,
    GoalLanePhaseGateObservation,
    GoalLanePhaseGateOutcome,
    GoalLanePhaseState,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseCurrentSourceV1,
    GoalPhaseDependency,
    GoalPhaseExecutionAuthorityV1,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    GoalPhaseNativeDocumentV4,
    GoalPhaseOperationJournalEntryV1,
    GoalPhaseOperationJournalV1,
    decode_goal_phase_eligibility_decision,
    observe_goal_phase_eligibility,
    observe_goal_phase_eligibility_v2,
    decode_goal_phase_eligibility_decision_v2,
)


def _object_authority(*, dependency: bool = False) -> dict[str, object]:
    goal_tag = "goal/2026-09-26/object-eligibility"
    revision = "object-revision:sha256:" + "a" * 64
    coordinate = GoalPhaseCoordinate(goal_tag, "runtime", "first")
    gate = GoalLanePhaseGate(
        gate_key="first", promise="First gate.",
        gate_contract_ref="contract:first", evidence_schema_ref="evidence:first",
    )
    predecessor = GoalPhaseCoordinate(goal_tag, "runtime", "predecessor")
    predecessor_gate = GoalLanePhaseGate(
        gate_key="predecessor", promise="Predecessor gate.",
        gate_contract_ref="contract:predecessor", evidence_schema_ref="evidence:predecessor",
    )
    document = GoalPhaseNativeDocumentV2(
        goal_tag=goal_tag,
        compatibility_projection_sha256="sha256:" + "b" * 64,
        compatibility_projection_byte_count=10,
        definitions=(GoalLanePhaseDefinitionV1(
            coordinate=coordinate, ordinal=1, gate=gate,
            title="First", intent="Prove object-provider parity.",
        ),) + ((GoalLanePhaseDefinitionV1(
            coordinate=predecessor, ordinal=2, gate=predecessor_gate,
            title="Predecessor", intent="Remain definition-only.",
        ),) if dependency else ()),
        operational_bundle=GoalPhaseContractBundleV1(phases=(GoalLanePhase(
            coordinate=coordinate, title="First", ordinal=1,
            intent="Prove object-provider parity.",
            state=GoalLanePhaseState.ACTIVE, gate=gate,
        ),), dependencies=((GoalPhaseDependency(
            owner_goal_tag=goal_tag, dependency_key="first-requires-predecessor",
            dependent=coordinate, prerequisite=predecessor,
            required_gate_digest=predecessor_gate.gate_digest,
            relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
            reason="Authored prerequisite.",
        ),) if dependency else ())),
        unresolved_dependencies=(), source_refs=("object-source:goal",),
        execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
            proposal_aggregate_ref="goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64,
            coordinator_acceptance_ref="goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:" + "3" * 64,
        ),
    )
    global_authority = GoalGlobalDirectionAuthorityV1(
        goal_tag=goal_tag, lifecycle_status="active", owner_ref="owner:one",
        governance_authority_refs=(), hold_state="clear", hold_authority_refs=(),
        execution_authority_ref=document.execution_authority.authority_ref,
        compatibility_guard_ref="guard:one", source_revision_ref=revision,
        projector_ref="object-projector:v1", projection_receipt_ref="object-projection:one",
    )
    lane_authority = GoalLaneDirectionAuthorityV1(
        goal_tag=goal_tag, lane_key="runtime", role="Runtime", owner_ref="owner:one",
        operational_state="ready", state_detail=None, blocker_authority_refs=(),
        current_issue_ref=None, current_issue_authority_ref=None,
        compatibility_guard_ref="guard:one", source_revision_ref=revision,
        projector_ref="object-projector:v1", projection_receipt_ref="object-projection:one",
    )
    return {
        "document": document, "coordinate": coordinate,
        "expected_gate_digest": gate.gate_digest,
        "global_authority": global_authority, "lane_authority": lane_authority,
        "source_revision_ref": revision,
        "whole_goal_currentness": GoalFrontierCurrentness.CURRENT,
        "phase_currentness": GoalFrontierCurrentness.CURRENT,
        "prerequisite_sources": {},
    }


def test_object_source_uses_the_same_neutral_eligibility_law() -> None:
    authority = _object_authority()
    decision = observe_goal_phase_eligibility(**authority)  # type: ignore[arg-type]
    assert decision.eligibility == "eligible"
    assert decision.dependency_gate.to_wire()["state"] == "satisfied"
    assert decision.observation_coverage == "none"
    assert decode_goal_phase_eligibility_decision(
        decision.to_wire(), **authority
    ) == decision


@pytest.mark.parametrize("dependency", [False, True])
def test_object_compatibility_source_v2_keeps_the_exact_v1_decision_law(dependency) -> None:
    args = _object_authority(dependency=dependency)
    old = observe_goal_phase_eligibility(**args)  # type: ignore[arg-type]
    result = observe_goal_phase_eligibility_v2(**args)  # type: ignore[arg-type]
    validate_goal_phase_eligibility_decision_v2_wire(result.to_wire())
    assert result.decision == old
    assert result.lane_authority_profile == "markdown_compat_v1"
    assert result.source_revision_ref.startswith("object-revision:")
    assert decode_goal_phase_eligibility_decision_v2(result.to_wire(), **args) == result  # type: ignore[arg-type]


@pytest.mark.parametrize("fault", ["unknown_profile", "running", "stale_eligible", "state_partition", "coverage"])
def test_neutral_wire_invariants_reject_contradictions_without_source_verification(fault):
    wire = observe_goal_phase_eligibility_v2(**_object_authority()).to_wire()  # type: ignore[arg-type]
    if fault == "unknown_profile":
        wire["lane_authority_profile"] = "unknown"
    elif fault == "running":
        wire["eligibility"] = "running"
    else:
        gate = wire["dependency_gate"]
        gate.update(state="stale", incoming_count=1, dependency_keys=["one"], stale=["one"])
        wire["observation_coverage"] = "complete"
        if fault == "state_partition":
            gate["state"] = "satisfied"
        elif fault == "coverage":
            wire.update(eligibility="held", reasons=["frontier_ineligible"], observation_coverage="none")
    with pytest.raises(ValueError):
        validate_goal_phase_eligibility_decision_v2_wire(wire)


@pytest.mark.parametrize("state", [GoalLanePhaseState.ACCEPTED, GoalLanePhaseState.WITHDRAWN])
@pytest.mark.parametrize("dependency", [False, True])
def test_neutral_v2_terminal_wire_preserves_non_authorizing_frontier(state, dependency):
    args = _object_authority(dependency=dependency)
    document = args["document"]
    phase = document.operational_bundle.phases[0]
    if state is GoalLanePhaseState.ACCEPTED:
        phase = replace(phase, state=state,
            gate_observations=(GoalLanePhaseGateObservation(
                observation_ref="observation:accepted", gate_digest=phase.gate.gate_digest,
                outcome=GoalLanePhaseGateOutcome.SATISFIED, evaluator_ref="evaluator:terminal",
                evidence_refs=("evidence:accepted",), source_revision_refs=(args["source_revision_ref"],),
                evaluated_at="2026-10-01T00:00:00Z", currentness_ref="currentness:accepted"),),
            last_receipt_ref="goal-phase-acceptance:sha256:" + "d" * 64)
    else:
        phase = replace(phase, state=state)
    args["document"] = replace(document,
        operational_bundle=replace(document.operational_bundle, phases=(phase,)))
    decision = observe_goal_phase_eligibility_v2(**args).to_wire()
    validate_goal_phase_eligibility_decision_v2_wire(decision)
    assert decision["eligibility"] == "held"
    assert decision["dependency_gate"]["state"] == "not_applicable"


def test_v4_represented_lane_uses_compatibility_authority_not_native_guard() -> None:
    args = _object_authority()
    old = args["document"]
    assert type(old) is GoalPhaseNativeDocumentV2
    definition = replace(old.definitions[0], coordinate=GoalPhaseCoordinate(old.goal_tag, "foundation", "f1"))
    document = GoalPhaseNativeDocumentV4(
        goal_tag=old.goal_tag, compatibility_projection_sha256=old.compatibility_projection_sha256,
        compatibility_projection_byte_count=old.compatibility_projection_byte_count,
        definitions=(*old.definitions, definition), operational_bundle=old.operational_bundle,
        unresolved_dependencies=old.unresolved_dependencies, source_refs=old.source_refs,
        execution_authority=old.execution_authority,
        native_lane_authorities=(GoalNativeLaneAuthorityV1(
            goal_tag=old.goal_tag, lane_key="foundation", role="Foundation",
            owner_profile="provider_execution_v1", owner_ref="codex-owner", operational_state="planned",
            state_detail=None, hold_authority_refs=(), current_work_association_ref=None,
        ),), operation_journal_profile="none",
    )
    result = observe_goal_phase_eligibility_v2(**{**args, "document": document})  # type: ignore[arg-type]
    assert result.decision.eligibility == "eligible"
    assert result.lane_authority_profile == "markdown_compat_v1"
    with pytest.raises(TypeError, match="native V2 or V3"):
        observe_goal_phase_eligibility(**{**args, "document": document})  # type: ignore[arg-type]


def test_v3_journal_is_readable_but_does_not_mint_eligibility_or_approval() -> None:
    authority = _object_authority()
    prior = authority["document"]
    assert isinstance(prior, GoalPhaseNativeDocumentV2)
    coordinate = authority["coordinate"]
    assert isinstance(coordinate, GoalPhaseCoordinate)
    entry = GoalPhaseOperationJournalEntryV1(
        operation_kind="approve_pursuit", decision="approve",
        coordinate=coordinate, gate_digest=prior.definitions[0].gate.gate_digest,
        source_preimage_ref=prior.document_ref, actor_ref="identity:human-one",
        action_occurrence_ref="actor-action-occurrence:sha256:" + "1" * 64,
        policy_ref="goal-phase-approval-policy:sha256:" + "2" * 64,
        policy_digest="sha256:" + "3" * 64,
        idempotency_key="approve-first", delta_ref="goal-phase-delta:sha256:" + "4" * 64,
        event_ref="goal-phase-event:sha256:" + "5" * 64,
    )
    successor = GoalPhaseNativeDocumentV3(
        goal_tag=prior.goal_tag,
        compatibility_projection_sha256=prior.compatibility_projection_sha256,
        compatibility_projection_byte_count=prior.compatibility_projection_byte_count,
        definitions=prior.definitions, operational_bundle=prior.operational_bundle,
        unresolved_dependencies=prior.unresolved_dependencies,
        source_refs=prior.source_refs, execution_authority=prior.execution_authority,
        phase_operation_journal=GoalPhaseOperationJournalV1((entry,)),
    )
    v2_decision = observe_goal_phase_eligibility(**authority)  # type: ignore[arg-type]
    v3_authority = {**authority, "document": successor}
    v3_decision = observe_goal_phase_eligibility(**v3_authority)  # type: ignore[arg-type]
    assert v3_decision.document_ref == successor.document_ref
    assert v3_decision.eligibility == v2_decision.eligibility
    assert v3_decision.reasons == v2_decision.reasons
    assert v3_decision.dependency_gate == v2_decision.dependency_gate
    assert decode_goal_phase_eligibility_decision(
        v3_decision.to_wire(), **v3_authority  # type: ignore[arg-type]
    ) == v3_decision
    with pytest.raises(ValueError, match="qualified authority"):
        decode_goal_phase_eligibility_decision(
            v2_decision.to_wire(), **v3_authority  # type: ignore[arg-type]
        )


def test_object_source_preserves_missing_observation_as_not_evaluated() -> None:
    authority = _object_authority(dependency=True)
    decision = observe_goal_phase_eligibility(**authority)  # type: ignore[arg-type]
    assert decision.eligibility == "held"
    assert decision.dependency_gate.to_wire()["not_evaluated"] == [
        "first-requires-predecessor"
    ]
    assert decision.reasons == ("frontier_ineligible",)


@pytest.mark.parametrize(
    "source_revision_refs",
    [
        ("historical-source:before-publication",),
        (
            "historical-source:before-publication",
            "historical-source:later-publication",
        ),
    ],
    ids=("one-historical-revision", "multiple-historical-revisions"),
)
def test_historical_gate_evidence_cannot_be_relabelled_current(
    source_revision_refs: tuple[str, ...],
) -> None:
    authority = _object_authority(dependency=True)
    document = authority["document"]
    assert type(document) is GoalPhaseNativeDocumentV2
    predecessor = document.definitions[1]
    current_phase = GoalLanePhase(
        coordinate=predecessor.coordinate, ordinal=predecessor.ordinal,
        title=predecessor.title or "", intent=predecessor.intent or "",
        state=GoalLanePhaseState.ACCEPTED, gate=predecessor.gate,
        gate_observations=(GoalLanePhaseGateObservation(
            observation_ref="historical-gate-observation:predecessor",
            gate_digest=predecessor.gate.gate_digest,
            outcome=GoalLanePhaseGateOutcome.SATISFIED,
            evaluator_ref="evaluator:predecessor",
            evidence_refs=("evidence:predecessor",),
            source_revision_refs=source_revision_refs,
            evaluated_at="2026-09-26T16:00:00Z",
            currentness_ref="claimed-currentness:even-though-source-is-historical",
        ),),
        last_receipt_ref="goal-phase-acceptance:sha256:" + "a" * 64,
    )
    authority["document"] = replace(
        document,
        operational_bundle=GoalPhaseContractBundleV1(
            phases=document.operational_bundle.phases + (current_phase,),
            dependencies=document.operational_bundle.dependencies,
        ),
    )
    decision = observe_goal_phase_eligibility(**authority)  # type: ignore[arg-type]
    assert decision.eligibility == "held"
    assert decision.dependency_gate.to_wire()["stale"] == [
        "first-requires-predecessor"
    ]
    assert decision.dependency_gate.to_wire()["not_evaluated"] == []
    assert decision.observation_coverage == "complete"


def test_current_evaluator_gate_evidence_can_satisfy_dependency() -> None:
    authority = _object_authority(dependency=True)
    document = authority["document"]
    revision = authority["source_revision_ref"]
    assert type(document) is GoalPhaseNativeDocumentV2
    assert type(revision) is str
    predecessor = document.definitions[1]
    phase = GoalLanePhase(
        coordinate=predecessor.coordinate, ordinal=predecessor.ordinal,
        title=predecessor.title or "", intent=predecessor.intent or "",
        state=GoalLanePhaseState.ACCEPTED, gate=predecessor.gate,
        gate_observations=(GoalLanePhaseGateObservation(
            observation_ref="current-gate-observation:predecessor",
            gate_digest=predecessor.gate.gate_digest,
            outcome=GoalLanePhaseGateOutcome.SATISFIED,
            evaluator_ref="evaluator:predecessor",
            evidence_refs=("evidence:predecessor",),
            source_revision_refs=(revision,),
            evaluated_at="2026-09-26T16:00:00Z",
            currentness_ref="qualified-currentness:predecessor",
        ),),
        last_receipt_ref="goal-phase-acceptance:sha256:" + "a" * 64,
    )
    authority["document"] = replace(
        document,
        operational_bundle=GoalPhaseContractBundleV1(
            phases=document.operational_bundle.phases + (phase,),
            dependencies=document.operational_bundle.dependencies,
        ),
    )
    decision = observe_goal_phase_eligibility(**authority)  # type: ignore[arg-type]
    assert decision.eligibility == "eligible"
    assert decision.dependency_gate.to_wire()["satisfied"] == [
        "first-requires-predecessor"
    ]


def test_current_phase_source_cannot_be_substituted_or_unrelated() -> None:
    authority = _object_authority(dependency=True)
    document = authority["document"]
    assert type(document) is GoalPhaseNativeDocumentV2
    revision = authority["source_revision_ref"]
    assert type(revision) is str
    authority["prerequisite_sources"] = {
        document.goal_tag: GoalPhaseCurrentSourceV1(document, revision)
    }
    with pytest.raises(ValueError, match="dependent_source_must_not_be_substituted"):
        observe_goal_phase_eligibility(**authority)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("state", "outcome", "partition"),
    [
        (GoalLanePhaseState.ACTIVE, GoalLanePhaseGateOutcome.SATISFIED, "pending"),
        (GoalLanePhaseState.ACTIVE, GoalLanePhaseGateOutcome.REJECTED, "rejected"),
        (GoalLanePhaseState.ACTIVE, GoalLanePhaseGateOutcome.STALE, "stale"),
        (GoalLanePhaseState.ACTIVE, GoalLanePhaseGateOutcome.UNRESOLVED, "unresolved"),
        (GoalLanePhaseState.WITHDRAWN, GoalLanePhaseGateOutcome.SATISFIED, "stale"),
    ],
)
def test_current_source_negative_outcomes_remain_distinct(
    state: GoalLanePhaseState,
    outcome: GoalLanePhaseGateOutcome,
    partition: str,
) -> None:
    authority = _object_authority(dependency=True)
    document = authority["document"]
    assert type(document) is GoalPhaseNativeDocumentV2
    predecessor = document.definitions[1]
    evidence = (
        ("evidence:predecessor",)
        if outcome in {GoalLanePhaseGateOutcome.SATISFIED, GoalLanePhaseGateOutcome.REJECTED}
        else ()
    )
    phase = GoalLanePhase(
        coordinate=predecessor.coordinate, ordinal=predecessor.ordinal,
        title=predecessor.title or "", intent=predecessor.intent or "",
        state=state, gate=predecessor.gate,
        gate_observations=(GoalLanePhaseGateObservation(
            observation_ref=f"gate-observation:{outcome.value}",
            gate_digest=predecessor.gate.gate_digest,
            outcome=outcome, evaluator_ref="evaluator:predecessor",
            evidence_refs=evidence,
            source_revision_refs=(str(authority["source_revision_ref"]),),
            evaluated_at="2026-09-26T16:00:00Z",
            currentness_ref="historical-currentness:predecessor",
        ),),
    )
    authority["document"] = replace(
        document,
        operational_bundle=GoalPhaseContractBundleV1(
            phases=document.operational_bundle.phases + (phase,),
            dependencies=document.operational_bundle.dependencies,
        ),
    )
    decision = observe_goal_phase_eligibility(**authority)  # type: ignore[arg-type]
    assert decision.eligibility == "held"
    assert decision.dependency_gate.to_wire()[partition] == [
        "first-requires-predecessor"
    ]


def test_withdrawn_satisfaction_is_observed_but_explicitly_disqualified() -> None:
    authority = _object_authority(dependency=True)
    document = authority["document"]
    assert type(document) is GoalPhaseNativeDocumentV2
    predecessor = document.definitions[1]
    withdrawn = GoalLanePhase(
        coordinate=predecessor.coordinate, ordinal=predecessor.ordinal,
        title=predecessor.title or "", intent=predecessor.intent or "",
        state=GoalLanePhaseState.WITHDRAWN, gate=predecessor.gate,
        gate_observations=(GoalLanePhaseGateObservation(
            observation_ref="gate-observation:withdrawn-satisfaction",
            gate_digest=predecessor.gate.gate_digest,
            outcome=GoalLanePhaseGateOutcome.SATISFIED,
            evaluator_ref="evaluator:predecessor",
            evidence_refs=("evidence:predecessor",),
            source_revision_refs=("historical-source:predecessor",),
            evaluated_at="2026-09-26T16:00:00Z",
            currentness_ref="historical-currentness:predecessor",
        ),),
    )
    authority["document"] = replace(
        document,
        operational_bundle=GoalPhaseContractBundleV1(
            phases=document.operational_bundle.phases + (withdrawn,),
            dependencies=document.operational_bundle.dependencies,
        ),
    )
    decision = observe_goal_phase_eligibility(**authority)  # type: ignore[arg-type]
    assert decision.eligibility == "held"
    assert decision.observation_coverage == "complete"
    assert decision.dependency_gate.to_wire()["stale"] == [
        "first-requires-predecessor"
    ]
    assert decision.dependency_gate.to_wire()["not_evaluated"] == []


def test_redigested_or_retyped_decision_cannot_change_neutral_result() -> None:
    authority = _object_authority()
    wire = observe_goal_phase_eligibility(**authority).to_wire()  # type: ignore[arg-type]
    changed = deepcopy(wire)
    changed["eligibility"] = "held"
    changed["reasons"] = ["frontier_ineligible"]
    with pytest.raises(ValueError, match="differs"):
        decode_goal_phase_eligibility_decision(changed, **authority)
    changed = deepcopy(wire)
    changed["dependency_gate"]["incoming_count"] = False
    with pytest.raises(ValueError, match="differs"):
        decode_goal_phase_eligibility_decision(changed, **authority)
