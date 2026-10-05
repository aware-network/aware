"""Provider-independent, read-only native Phase eligibility decision.

Source adapters qualify the document and direction authority before invoking
this operation. Neither filesystem coordinates nor Issue/dispatch effects enter
the decision contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, cast

from .phase_contracts import (
    GoalLanePhaseState,
    GoalLanePhaseGateOutcome,
    GoalLanePhaseWorkDisposition,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
)
from .phase_document import GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3
from .phase_frontier import (
    GoalFrontierCurrentness,
    GoalFrontierProjectionHealth,
    GoalPhaseDependencyObservationV2,
    GoalPhaseFrontierDependencyGateV2,
    GoalPhaseFrontierEligibility,
    goal_phase_dependency_digest,
    observe_goal_phase_dependency,
    observe_unresolved_goal_phase_dependency,
    project_goal_phase_frontier,
)
from .phase_native_scope_advancement import (
    GoalGlobalDirectionAuthorityV1,
    GoalLaneDirectionAuthorityV1,
)


class GoalPhaseEligibilityError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class GoalPhaseCurrentSourceV1:
    """A source adapter's independently qualified, current native Goal source."""

    document: GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3
    source_revision_ref: str

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseCurrentSourceV1:
            raise TypeError("current source type must be exact")
        if type(self.document) not in {GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3}:
            raise TypeError("current source requires native V2 or V3 document")
        self.document.__post_init__()
        if type(self.source_revision_ref) is not str or not self.source_revision_ref:
            raise ValueError("current source revision is missing")


@dataclass(frozen=True, slots=True)
class GoalPhaseEligibilityDecisionV1:
    coordinate: GoalPhaseCoordinate
    document_ref: str
    gate_digest: str
    goal_authority_ref: str
    lane_authority_ref: str
    observation_coverage: str
    phase_state: str
    projection_health: str
    dependency_gate: GoalPhaseFrontierDependencyGateV2
    unresolved_dependency_keys: tuple[str, ...]
    eligibility: str
    reasons: tuple[str, ...]

    def to_wire(self) -> dict[str, object]:
        return {
            "native_document_ref": self.document_ref,
            "gate_digest": self.gate_digest,
            "goal_authority_ref": self.goal_authority_ref,
            "lane_authority_ref": self.lane_authority_ref,
            "observation_coverage": self.observation_coverage,
            "phase_state": self.phase_state,
            "projection_health": self.projection_health,
            "dependency_gate": self.dependency_gate.to_wire(),
            "unresolved_dependency_keys": list(self.unresolved_dependency_keys),
            "eligibility": self.eligibility,
            "reasons": list(self.reasons),
        }


def observe_goal_phase_eligibility(
    *,
    document: GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3,
    coordinate: GoalPhaseCoordinate,
    expected_gate_digest: str,
    global_authority: GoalGlobalDirectionAuthorityV1,
    lane_authority: GoalLaneDirectionAuthorityV1,
    source_revision_ref: str,
    whole_goal_currentness: GoalFrontierCurrentness,
    phase_currentness: GoalFrontierCurrentness,
    prerequisite_sources: Mapping[str, GoalPhaseCurrentSourceV1] | None = None,
) -> GoalPhaseEligibilityDecisionV1:
    """Decide once from qualified authority, using the canonical frontier.

    The source adapter must prove that its source revision and authority inputs
    are current. This function never grants Issue admission or dispatch.
    """

    if type(document) not in {GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3}:
        raise TypeError("document must be native V2 or V3")
    if type(coordinate) is not GoalPhaseCoordinate:
        raise TypeError("coordinate must be exact")
    if type(global_authority) is not GoalGlobalDirectionAuthorityV1:
        raise TypeError("global authority must be exact")
    if type(lane_authority) is not GoalLaneDirectionAuthorityV1:
        raise TypeError("lane authority must be exact")
    document.__post_init__()
    global_authority.__post_init__()
    lane_authority.__post_init__()
    if (
        document.goal_tag != coordinate.goal_tag
        or global_authority.goal_tag != coordinate.goal_tag
        or lane_authority.goal_tag != coordinate.goal_tag
        or lane_authority.lane_key != coordinate.lane_key
    ):
        raise GoalPhaseEligibilityError("authority_coordinate_mismatch")
    if (
        global_authority.source_revision_ref != source_revision_ref
        or lane_authority.source_revision_ref != source_revision_ref
    ):
        raise GoalPhaseEligibilityError("authority_source_mismatch")
    definitions = tuple(
        definition for definition in document.definitions
        if definition.coordinate == coordinate
    )
    if len(definitions) != 1:
        raise GoalPhaseEligibilityError("phase_definition_absent")
    if definitions[0].gate.gate_digest != expected_gate_digest:
        raise GoalPhaseEligibilityError("gate_digest_mismatch")
    phases = tuple(
        phase for phase in document.operational_bundle.phases
        if phase.coordinate == coordinate
    )
    if len(phases) != 1:
        raise GoalPhaseEligibilityError("phase_not_operational")
    incoming = tuple(
        dependency for dependency in document.operational_bundle.dependencies
        if dependency.dependent == coordinate
    )
    unresolved = tuple(
        dependency for dependency in document.unresolved_dependencies
        if dependency.dependent == coordinate
    )
    sources = {} if prerequisite_sources is None else dict(prerequisite_sources)
    if coordinate.goal_tag in sources:
        raise GoalPhaseEligibilityError("dependent_source_must_not_be_substituted")
    if any(
        type(source) is not GoalPhaseCurrentSourceV1 or source.document.goal_tag != tag
        for tag, source in sources.items()
    ):
        raise GoalPhaseEligibilityError("prerequisite_source_coordinate_mismatch")
    required_external = {
        dependency.prerequisite.goal_tag for dependency in incoming
        if dependency.prerequisite.goal_tag != coordinate.goal_tag
    }
    if set(sources) - required_external:
        raise GoalPhaseEligibilityError("unrelated_prerequisite_source")
    dependent_source = GoalPhaseCurrentSourceV1(document, source_revision_ref)
    all_sources = {coordinate.goal_tag: dependent_source, **sources}
    supplied: dict[str, GoalPhaseDependencyObservationV2] = {}
    for dependency in incoming:
        source = all_sources.get(dependency.prerequisite.goal_tag)
        if source is None:
            continue
        source.__post_init__()
        observed = _observe_current_dependency(
            dependency=dependency,
            dependent_source=dependent_source,
            prerequisite_source=source,
        )
        if observed is not None:
            supplied[dependency.dependency_key] = observed
    frontier = project_goal_phase_frontier(
        goal_tag=coordinate.goal_tag,
        source_revision_ref=source_revision_ref,
        whole_goal_currentness=whole_goal_currentness,
        bundle=GoalPhaseContractBundleV1(phases=phases, dependencies=incoming),
        observations=supplied,
        phase_currentness={coordinate: phase_currentness},
        lane_projection_health={
            coordinate.lane_key: (
                GoalFrontierProjectionHealth.CLEAN
                if lane_authority.qualification == "qualified"
                else GoalFrontierProjectionHealth.AMBIGUOUS
            )
        },
        current_revision_by_goal={
            tag: source.source_revision_ref for tag, source in all_sources.items()
        },
    )
    projection = frontier.lanes[0].phases[0]
    reasons: list[str] = []
    if (
        global_authority.lifecycle_status != "active"
        or global_authority.hold_state != "clear"
    ):
        reasons.append("goal_not_active")
    if lane_authority.qualification != "qualified":
        reasons.append("lane_authority_ambiguous")
    current_work = tuple(
        work.issue_ref
        for candidate in document.operational_bundle.phases
        if candidate.coordinate.lane_key == coordinate.lane_key
        for work in candidate.work_associations
        if work.disposition is GoalLanePhaseWorkDisposition.CURRENT
    )
    expected_issue = lane_authority.current_issue_ref
    work_agrees = (
        not current_work
        if expected_issue is None or expected_issue.startswith("TBD:")
        else current_work == (expected_issue,)
    )
    if not work_agrees:
        reasons.append("lane_native_work_disagreement")
    if lane_authority.operational_state not in {"active", "ready", "planned"}:
        reasons.append("lane_not_open")
    if phases[0].state not in {GoalLanePhaseState.ACTIVE, GoalLanePhaseState.PLANNED}:
        reasons.append("phase_not_pursuable")
    if unresolved:
        reasons.append("unresolved_incoming_dependency")
    if projection.admission_eligibility is not GoalPhaseFrontierEligibility.ELIGIBLE:
        reasons.append("frontier_ineligible")
    coverage = "none" if not supplied else (
        "complete" if len(supplied) == len(incoming) else "partial"
    )
    return GoalPhaseEligibilityDecisionV1(
        coordinate=coordinate,
        document_ref=document.document_ref,
        gate_digest=definitions[0].gate.gate_digest,
        goal_authority_ref=global_authority.authority_ref,
        lane_authority_ref=lane_authority.authority_ref,
        observation_coverage=coverage,
        phase_state=phases[0].state.value,
        projection_health=projection.projection_health.value,
        dependency_gate=projection.dependency_gate,
        unresolved_dependency_keys=tuple(sorted(item.dependency_key for item in unresolved)),
        eligibility="eligible" if not reasons else "held",
        reasons=tuple(sorted(reasons)),
    )


def decode_goal_phase_eligibility_decision(
    payload: Mapping[str, object],
    *,
    document: GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3,
    coordinate: GoalPhaseCoordinate,
    expected_gate_digest: str,
    global_authority: GoalGlobalDirectionAuthorityV1,
    lane_authority: GoalLaneDirectionAuthorityV1,
    source_revision_ref: str,
    whole_goal_currentness: GoalFrontierCurrentness,
    phase_currentness: GoalFrontierCurrentness,
    prerequisite_sources: Mapping[str, GoalPhaseCurrentSourceV1] | None = None,
) -> GoalPhaseEligibilityDecisionV1:
    """Strictly rederive a transported decision from independent typed inputs."""

    if type(payload) is not dict:
        raise TypeError("decision payload must be an exact JSON object")
    expected = observe_goal_phase_eligibility(
        document=document,
        coordinate=coordinate,
        expected_gate_digest=expected_gate_digest,
        global_authority=global_authority,
        lane_authority=lane_authority,
        source_revision_ref=source_revision_ref,
        whole_goal_currentness=whole_goal_currentness,
        phase_currentness=phase_currentness,
        prerequisite_sources=prerequisite_sources,
    )
    if not _exact_wire_equal(payload, expected.to_wire()):
        raise ValueError("eligibility decision differs from qualified authority")
    return expected


def _observe_current_dependency(
    *,
    dependency: GoalPhaseDependency,
    dependent_source: GoalPhaseCurrentSourceV1,
    prerequisite_source: GoalPhaseCurrentSourceV1,
) -> GoalPhaseDependencyObservationV2 | None:
    """Carry the Gate's actual evidence epoch into the canonical frontier."""

    phases = tuple(
        phase for phase in prerequisite_source.document.operational_bundle.phases
        if phase.coordinate == dependency.prerequisite
    )
    if len(phases) != 1:
        return None
    phase = phases[0]
    current = tuple(
        item for item in phase.gate_observations
        if item.outcome is not GoalLanePhaseGateOutcome.STALE
    )
    if len(current) == 1:
        gate_observation = current[0]
    elif not current and len(phase.gate_observations) == 1:
        gate_observation = phase.gate_observations[0]
    else:
        return None
    # A current carrier can retain an older Gate observation. Its presence
    # cannot advance that observation's source epoch. Without independently
    # verified scope-advancement evidence, the canonical frontier must see the
    # historical revision and classify it stale rather than satisfied.
    if gate_observation.outcome is GoalLanePhaseGateOutcome.UNRESOLVED:
        return observe_unresolved_goal_phase_dependency(
            dependency,
            evaluator_ref="goal-phase-dependency-read-evaluator:v1",
            currentness_ref=gate_observation.currentness_ref,
        )
    withdrawn_satisfaction = (
        gate_observation.outcome is GoalLanePhaseGateOutcome.SATISFIED
        and phase.state is GoalLanePhaseState.WITHDRAWN
    )
    evidence_revisions = gate_observation.source_revision_refs
    if prerequisite_source.source_revision_ref in evidence_revisions:
        evidence_revision = prerequisite_source.source_revision_ref
    else:
        # The Gate observation guarantees at least one source revision. Carry
        # its canonical first evidenced revision; the frontier compares it to
        # the current prerequisite epoch and reports stale, never unevaluated
        # or satisfied, when all evidenced revisions are historical.
        evidence_revision = evidence_revisions[0]
    if withdrawn_satisfaction:
        return GoalPhaseDependencyObservationV2(
            dependency_key=dependency.dependency_key,
            dependency_digest=goal_phase_dependency_digest(dependency),
            dependent=dependency.dependent,
            prerequisite=dependency.prerequisite,
            required_gate_digest=dependency.required_gate_digest,
            relation=dependency.relation,
            outcome=GoalLanePhaseGateOutcome.STALE,
            dependent_source_revision_ref=dependent_source.source_revision_ref,
            prerequisite_source_revision_ref=evidence_revision,
            prerequisite_phase_state=phase.state,
            prerequisite_gate_observation_ref=gate_observation.observation_ref,
            prerequisite_acceptance_receipt_ref=None,
            evidence_refs=gate_observation.evidence_refs,
            evaluator_ref="goal-phase-dependency-read-evaluator:v1",
            currentness_ref=gate_observation.currentness_ref,
        )
    return observe_goal_phase_dependency(
        dependency,
        dependent_source_revision_ref=dependent_source.source_revision_ref,
        prerequisite_source_revision_ref=evidence_revision,
        prerequisite_phase=phase,
        evaluator_ref="goal-phase-dependency-read-evaluator:v1",
        currentness_ref=gate_observation.currentness_ref,
    )


def _exact_wire_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        left_map = cast(dict[object, object], left)
        right_map = cast(dict[object, object], right)
        return left_map.keys() == right_map.keys() and all(
            _exact_wire_equal(left_map[key], right_map[key]) for key in left_map
        )
    if type(left) is list:
        left_list = cast(list[object], left)
        right_list = cast(list[object], right)
        return len(left_list) == len(right_list) and all(
            _exact_wire_equal(a, b) for a, b in zip(left_list, right_list)
        )
    return left == right
