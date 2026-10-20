"""Provider-independent, read-only native Phase eligibility decision.

Source adapters qualify the document and direction authority before invoking
this operation. Neither filesystem coordinates nor Issue/dispatch effects enter
the decision contract.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from collections.abc import Mapping
from typing import cast

from .phase_contracts import (
    GoalLanePhaseState,
    GoalLanePhase,
    GoalLanePhaseGateOutcome,
    GoalLanePhaseWorkDisposition,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
)
from .phase_document import (
    GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3, GoalPhaseNativeDocumentV4,
    encode_goal_phase_native_document,
)
from .frontier import GoalFrontierCurrentness, GoalFrontierProjectionHealth
from .identity import fingerprint
from .phase_native_lane_authority import (
    GoalNativeLaneDirectionAuthorityV1,
    require_qualified_goal_native_lane_direction,
)
from .phase_native_lane_evidence import observe_native_lane_gate_phases
from .phase_frontier import (
    GoalPhaseDependencyObservationV2,
    GoalPhaseFrontierDependencyGateV2,
    GoalPhaseFrontierDependencyGateState,
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
        self.code: str = code
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
class GoalPhaseCurrentSourceV2:
    """Versioned source facts for V2/V3/V4, not an authority issuer."""

    document: GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3 | GoalPhaseNativeDocumentV4
    source_revision_ref: str

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseCurrentSourceV2:
            raise TypeError("current source V2 type must be exact")
        if type(self.document) not in {GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3, GoalPhaseNativeDocumentV4}:
            raise TypeError("current source V2 requires native V2/V3/V4 document")
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
    return _reduce_goal_phase_eligibility(
        document=document, coordinate=coordinate, expected_gate_digest=expected_gate_digest,
        global_authority=global_authority, lane_authority_ref=lane_authority.authority_ref,
        lane_qualification=lane_authority.qualification,
        lane_state=lane_authority.operational_state, current_issue_ref=lane_authority.current_issue_ref,
        source_revision_ref=source_revision_ref, whole_goal_currentness=whole_goal_currentness,
        phase_currentness=phase_currentness, prerequisite_sources=prerequisite_sources,
        source_type=GoalPhaseCurrentSourceV1,
    )


def _reduce_goal_phase_eligibility(
    *, document: GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3 | GoalPhaseNativeDocumentV4,
    coordinate: GoalPhaseCoordinate, expected_gate_digest: str,
    global_authority: GoalGlobalDirectionAuthorityV1, lane_authority_ref: str,
    lane_qualification: str, lane_state: str, current_issue_ref: str | None,
    source_revision_ref: str, whole_goal_currentness: GoalFrontierCurrentness,
    phase_currentness: GoalFrontierCurrentness,
    prerequisite_sources: Mapping[str, GoalPhaseCurrentSourceV1 | GoalPhaseCurrentSourceV2] | None,
    source_type: type[GoalPhaseCurrentSourceV1] | type[GoalPhaseCurrentSourceV2],
    observed_phases: Mapping[GoalPhaseCoordinate, GoalLanePhase] | None = None,
) -> GoalPhaseEligibilityDecisionV1:
    """The single decision law; versioned entrances qualify provenance first."""
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
        type(source) is not source_type or source.document.goal_tag != tag
        for tag, source in sources.items()
    ):
        raise GoalPhaseEligibilityError("prerequisite_source_coordinate_mismatch")
    required_external = {
        dependency.prerequisite.goal_tag for dependency in incoming
        if dependency.prerequisite.goal_tag != coordinate.goal_tag
    }
    if set(sources) - required_external:
        raise GoalPhaseEligibilityError("unrelated_prerequisite_source")
    if source_type is GoalPhaseCurrentSourceV1:
        dependent_source = GoalPhaseCurrentSourceV1(
            cast(GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3, document), source_revision_ref,
        )
    else:
        dependent_source = GoalPhaseCurrentSourceV2(document, source_revision_ref)
    all_sources = {coordinate.goal_tag: dependent_source, **sources}
    views = {} if observed_phases is None else dict(observed_phases)
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
            observed_phase=views.get(dependency.prerequisite),
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
                if lane_qualification == "qualified"
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
    if lane_qualification != "qualified":
        reasons.append("lane_authority_ambiguous")
    current_work = tuple(
        work.issue_ref
        for candidate in document.operational_bundle.phases
        if candidate.coordinate.lane_key == coordinate.lane_key
        for work in candidate.work_associations
        if work.disposition is GoalLanePhaseWorkDisposition.CURRENT
    )
    expected_issue = current_issue_ref
    work_agrees = (
        not current_work
        if expected_issue is None or expected_issue.startswith("TBD:")
        else current_work == (expected_issue,)
    )
    if not work_agrees:
        reasons.append("lane_native_work_disagreement")
    if lane_state not in {"active", "ready", "planned"}:
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
        lane_authority_ref=lane_authority_ref,
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
    if not _exact_wire_equal(cast(dict[str, object], payload), expected.to_wire()):
        raise ValueError("eligibility decision differs from qualified authority")
    return expected


@dataclass(frozen=True, slots=True)
class GoalPhaseEligibilityDecisionV2:
    decision: GoalPhaseEligibilityDecisionV1
    lane_authority_profile: str
    source_revision_ref: str
    source_binding_ref: str
    scope_currentness_ref: str

    def to_wire(self) -> dict[str, object]:
        coordinate = self.decision.coordinate
        body = {
            "schema_id": "aware.goal.phase-eligibility-decision.v2",
            "coordinate": {"goal_tag": coordinate.goal_tag, "lane_key": coordinate.lane_key,
                "phase_key": coordinate.phase_key},
            "lane_authority_profile": self.lane_authority_profile,
            "source_revision_ref": self.source_revision_ref,
            "source_binding_ref": self.source_binding_ref,
            "scope_currentness_ref": self.scope_currentness_ref,
            "effect_profile": "read_only_non_authorizing",
            "event_effect": "none", "dispatch_effect": "none",
            **self.decision.to_wire(),
        }
        validate_goal_phase_eligibility_decision_v2_wire(body)
        return {**body, "decision_ref": "goal-phase-eligibility-decision:" + fingerprint(body)}


def validate_goal_phase_eligibility_decision_v2_wire(payload: Mapping[str, object]) -> None:
    """Check closed values and authority-free consistency, not source authority.

    Transport consumers use this neutral contract check without interpreting
    sources or evaluating eligibility. Passing it never authenticates a result;
    effectful entrances must still verify authority and rerun the decision law.
    Schema, request bindings and content references are checked by the transport.
    """
    def closed(name: str, values: set[str]) -> str:
        value = payload.get(name)
        if type(value) is not str or value not in values:
            raise ValueError(f"eligibility V2 {name} unsupported")
        return value

    def members(value: object) -> tuple[str, ...]:
        if type(value) is not list:
            raise ValueError("eligibility V2 partition must be an exact list")
        items = cast(list[object], value)
        if any(type(item) is not str or not item for item in items):
            raise ValueError("eligibility V2 partition must contain text")
        result = tuple(cast(list[str], items))
        if result != tuple(sorted(set(result))):
            raise ValueError("eligibility V2 partition must be canonical")
        return result

    closed("lane_authority_profile", {"native_carrier_v1", "markdown_compat_v1"})
    coverage = closed("observation_coverage", {"none", "partial", "complete"})
    phase_state = closed("phase_state", {state.value for state in GoalLanePhaseState})
    health = closed("projection_health", {state.value for state in GoalFrontierProjectionHealth})
    eligibility = closed("eligibility", {"eligible", "held"})
    reasons = members(payload.get("reasons"))
    if set(reasons) - {"goal_not_active", "lane_authority_ambiguous", "lane_native_work_disagreement",
        "lane_not_open", "phase_not_pursuable", "unresolved_incoming_dependency", "frontier_ineligible"}:
        raise ValueError("eligibility V2 reason unsupported")
    unresolved = members(payload.get("unresolved_dependency_keys"))
    gate_value = payload.get("dependency_gate")
    if type(gate_value) is not dict:
        raise ValueError("eligibility V2 dependency gate must be an exact object")
    gate = cast(dict[str, object], gate_value)
    partitions = ("satisfied", "pending", "not_evaluated", "stale", "unresolved", "rejected")
    if set(gate) != {"state", "incoming_count", "dependency_keys", *partitions}:
        raise ValueError("eligibility V2 dependency gate fields differ")
    state_value = gate["state"]
    if type(state_value) is not str:
        raise ValueError("eligibility V2 dependency state must be text")
    state = GoalPhaseFrontierDependencyGateState(state_value)
    keys = members(gate["dependency_keys"])
    groups = {name: members(gate[name]) for name in partitions}
    count = gate["incoming_count"]
    if type(count) is not int or count != len(keys):
        raise ValueError("eligibility V2 dependency count differs")
    if (count == 0 and coverage != "none") or (count < 2 and coverage == "partial"):
        raise ValueError("eligibility V2 coverage contradicts dependency count")
    terminal = phase_state in {"accepted", "withdrawn"}
    if terminal:
        if state is not GoalPhaseFrontierDependencyGateState.NOT_APPLICABLE or any(groups.values()):
            raise ValueError("eligibility V2 terminal dependency gate differs")
    else:
        flattened = tuple(key for group in groups.values() for key in group)
        if tuple(sorted(flattened)) != keys:
            raise ValueError("eligibility V2 dependency partitions differ")
        # Validate the aggregate's canonical precedence from its explicit
        # partitions only; this does not evaluate any prerequisite authority.
        expected_state = "satisfied"
        for partition, aggregate in (("rejected", "rejected"), ("unresolved", "unresolved"),
            ("stale", "stale"), ("not_evaluated", "held"), ("pending", "held")):
            if groups[partition]:
                expected_state = aggregate
                break
        if state.value != expected_state:
            raise ValueError("eligibility V2 dependency state contradicts partitions")
        observed_count = count - len(groups["not_evaluated"])
        expected_coverage = "none" if observed_count == 0 else (
            "complete" if observed_count == count else "partial")
        if coverage != expected_coverage:
            raise ValueError("eligibility V2 coverage contradicts partitions")
    if (eligibility == "eligible") != (not reasons):
        raise ValueError("eligibility V2 decision contradicts reasons")
    if ("phase_not_pursuable" in reasons) != (phase_state not in {"active", "planned"}):
        raise ValueError("eligibility V2 Phase state contradicts reasons")
    if ("unresolved_incoming_dependency" in reasons) != bool(unresolved):
        raise ValueError("eligibility V2 unresolved declarations contradict reasons")
    if (health != "clean" or state is not GoalPhaseFrontierDependencyGateState.SATISFIED) and (
        "frontier_ineligible" not in reasons
    ):
        raise ValueError("eligibility V2 frontier contradicts reasons")
    if eligibility == "eligible" and (
        phase_state not in {"active", "planned"} or health != "clean" or unresolved
        or state is not GoalPhaseFrontierDependencyGateState.SATISFIED
    ):
        raise ValueError("eligibility V2 eligible decision contradicts supplied facts")


def observe_goal_phase_eligibility_v2(
    *, document: GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3 | GoalPhaseNativeDocumentV4,
    coordinate: GoalPhaseCoordinate, expected_gate_digest: str,
    global_authority: GoalGlobalDirectionAuthorityV1,
    lane_authority: GoalLaneDirectionAuthorityV1 | GoalNativeLaneDirectionAuthorityV1,
    source_revision_ref: str,
    whole_goal_currentness: GoalFrontierCurrentness = GoalFrontierCurrentness.CURRENT,
    phase_currentness: GoalFrontierCurrentness = GoalFrontierCurrentness.CURRENT,
    prerequisite_sources: Mapping[str, GoalPhaseCurrentSourceV2] | None = None,
) -> GoalPhaseEligibilityDecisionV2:
    """Versioned provenance intake, one unchanged neutral decision law.

    Native authority is consumed only as an issued, immutable provider snapshot.
    It is current at its named observation, never perpetual effect authority.
    Later effectful operations must independently verify their own inputs again.
    """
    if type(document) not in {GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3, GoalPhaseNativeDocumentV4}:
        raise TypeError("eligibility V2 requires exact native V2/V3/V4 document")
    if type(coordinate) is not GoalPhaseCoordinate or type(global_authority) is not GoalGlobalDirectionAuthorityV1:
        raise TypeError("eligibility V2 requires exact coordinate/Goal authority")
    document.__post_init__()
    global_authority.__post_init__()
    if document.goal_tag != coordinate.goal_tag or global_authority.goal_tag != coordinate.goal_tag:
        raise GoalPhaseEligibilityError("authority_coordinate_mismatch")
    if global_authority.source_revision_ref != source_revision_ref:
        raise GoalPhaseEligibilityError("authority_source_mismatch")
    observed_phases: dict[GoalPhaseCoordinate, GoalLanePhase] = {}
    if type(lane_authority) is GoalNativeLaneDirectionAuthorityV1:
        qualified = require_qualified_goal_native_lane_direction(lane_authority)
        if (
            type(document) is not GoalPhaseNativeDocumentV4
            or qualified.lane_key != coordinate.lane_key
            or qualified.document.goal_tag != coordinate.goal_tag
        ):
            raise GoalPhaseEligibilityError("native_lane_authority_coordinate_mismatch")
        if (
            encode_goal_phase_native_document(document) != encode_goal_phase_native_document(qualified.document)
            or global_authority.to_wire() != qualified.global_authority.to_wire()
            or source_revision_ref != qualified.global_authority.source_revision_ref
        ):
            raise GoalPhaseEligibilityError("native_lane_authority_source_mismatch")
        if (
            whole_goal_currentness is not GoalFrontierCurrentness.CURRENT
            or phase_currentness is not GoalFrontierCurrentness.CURRENT
            or prerequisite_sources is not None
        ):
            raise GoalPhaseEligibilityError("native_lane_authority_must_not_be_substituted")
        lane = next(r for r in document.native_lane_authorities if r.lane_key == coordinate.lane_key)
        lane_ref, qualification, state = qualified.authority_ref, "qualified", lane.operational_state
        current_issue = next(iter(qualified.issue_authorities), None)
        sources = {tag: GoalPhaseCurrentSourceV2(source.document, source.source_revision_ref)
            for tag, source in qualified.dependency_sources.items() if tag != coordinate.goal_tag}
        # Scope contains outgoing as well as incoming edges. Only sources of
        # this Phase's incoming edges belong to its frontier decision.
        incoming_goals = {d.prerequisite.goal_tag for d in document.operational_bundle.dependencies if d.dependent == coordinate}
        sources = {tag: source for tag, source in sources.items() if tag in incoming_goals}
        profile = "native_carrier_v1"
        source_binding = "goal-native-lane-source:" + fingerprint({
            "document_ref": document.document_ref, "source_revision_ref": source_revision_ref,
            "source_blob_ref": qualified.source_blob_ref, "goal_sha256": qualified.goal_sha256,
        })
        scope_currentness = qualified.scope_currentness_ref
        if qualified.evidence_snapshot is not None and qualified.evidence_snapshot.gate_observations:
            observed_phases = observe_native_lane_gate_phases(
                document=document, evidence=qualified.evidence_snapshot,
                lane_key=coordinate.lane_key, source_revision_ref=source_revision_ref,
            )
    elif type(lane_authority) is GoalLaneDirectionAuthorityV1:
        lane_authority.__post_init__()
        if lane_authority.goal_tag != coordinate.goal_tag or lane_authority.lane_key != coordinate.lane_key:
            raise GoalPhaseEligibilityError("authority_coordinate_mismatch")
        if lane_authority.source_revision_ref != source_revision_ref:
            raise GoalPhaseEligibilityError("authority_source_mismatch")
        if type(document) is GoalPhaseNativeDocumentV4 and any(
            r.lane_key == coordinate.lane_key for r in document.native_lane_authorities
        ):
            raise GoalPhaseEligibilityError("native_lane_requires_native_provenance")
        lane_ref, qualification, state = lane_authority.authority_ref, lane_authority.qualification, lane_authority.operational_state
        current_issue = lane_authority.current_issue_ref
        sources = {} if prerequisite_sources is None else dict(prerequisite_sources)
        profile = "markdown_compat_v1"
        source_binding = lane_authority.projection_receipt_ref
        scope_currentness = global_authority.projection_receipt_ref
    else:
        raise TypeError("eligibility V2 lane authority profile must be exact")
    decision = _reduce_goal_phase_eligibility(
        document=document, coordinate=coordinate, expected_gate_digest=expected_gate_digest,
        global_authority=global_authority, lane_authority_ref=lane_ref,
        lane_qualification=qualification, lane_state=state, current_issue_ref=current_issue,
        source_revision_ref=source_revision_ref, whole_goal_currentness=whole_goal_currentness,
        phase_currentness=phase_currentness, prerequisite_sources=sources,
        source_type=GoalPhaseCurrentSourceV2,
        observed_phases=observed_phases,
    )
    return GoalPhaseEligibilityDecisionV2(
        decision=decision, lane_authority_profile=profile, source_revision_ref=source_revision_ref,
        source_binding_ref=source_binding, scope_currentness_ref=scope_currentness,
    )


def decode_goal_phase_eligibility_decision_v2(
    payload: Mapping[str, object], *,
    document: GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3 | GoalPhaseNativeDocumentV4,
    coordinate: GoalPhaseCoordinate, expected_gate_digest: str,
    global_authority: GoalGlobalDirectionAuthorityV1,
    lane_authority: GoalLaneDirectionAuthorityV1 | GoalNativeLaneDirectionAuthorityV1,
    source_revision_ref: str,
    whole_goal_currentness: GoalFrontierCurrentness = GoalFrontierCurrentness.CURRENT,
    phase_currentness: GoalFrontierCurrentness = GoalFrontierCurrentness.CURRENT,
    prerequisite_sources: Mapping[str, GoalPhaseCurrentSourceV2] | None = None,
) -> GoalPhaseEligibilityDecisionV2:
    """Recompute from independent authority, never a caller-supplied expected result."""
    if type(payload) is not dict:
        raise TypeError("decision V2 payload must be an exact JSON object")
    canonical = observe_goal_phase_eligibility_v2(
        document=document, coordinate=coordinate, expected_gate_digest=expected_gate_digest,
        global_authority=global_authority, lane_authority=lane_authority,
        source_revision_ref=source_revision_ref, whole_goal_currentness=whole_goal_currentness,
        phase_currentness=phase_currentness, prerequisite_sources=prerequisite_sources,
    )
    if not _exact_wire_equal(cast(dict[str, object], payload), canonical.to_wire()):
        raise ValueError("eligibility V2 decision differs from qualified authority")
    return canonical


def _observe_current_dependency(
    *,
    dependency: GoalPhaseDependency,
    dependent_source: GoalPhaseCurrentSourceV1 | GoalPhaseCurrentSourceV2,
    prerequisite_source: GoalPhaseCurrentSourceV1 | GoalPhaseCurrentSourceV2,
    observed_phase: GoalLanePhase | None = None,
) -> GoalPhaseDependencyObservationV2 | None:
    """Carry the Gate's actual evidence epoch into the canonical frontier."""

    phases = tuple(
        phase for phase in prerequisite_source.document.operational_bundle.phases
        if phase.coordinate == dependency.prerequisite
    )
    if len(phases) != 1:
        return None
    phase = phases[0]
    if observed_phase is not None:
        observed_phase.__post_init__()
        if replace(observed_phase, gate_observations=phase.gate_observations) != phase:
            raise GoalPhaseEligibilityError("qualified_gate_phase_view_mismatch")
        # This profile issues Gate evidence, not independent Phase acceptance.
        if dependency.relation.value == "requires_acceptance":
            raise GoalPhaseEligibilityError("native_lane_gate_acceptance_profile_unsupported")
        phase = observed_phase
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
