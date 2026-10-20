"""Phase-native dependency observation and frontier projection v2.

This module composes authored Phase dependencies, evaluator-owned Gate
observations, and caller-supplied currentness.  It does not parse Markdown,
infer edges from ordinals, inspect Issue lifecycle, emit events, or authorize
work.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import cast

from .dependencies import GoalDependencyRelation
from .frontier import GoalFrontierCurrentness, GoalFrontierProjectionHealth
from .identity import fingerprint, normalize_goal_tag, required_token
from .phase_contracts import (
    GoalLanePhase,
    GoalLanePhaseGateOutcome,
    GoalLanePhaseState,
    GoalLanePhaseWorkDisposition,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
)

GOAL_PHASE_FRONTIER_SCHEMA = "aware.goal.phase-frontier.v2"
GOAL_PHASE_DEPENDENCY_OBSERVATION_SCHEMA = (
    "aware.goal.phase-dependency-observation.v2"
)
_SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")
_ACCEPTANCE_RECEIPT_REF = re.compile(
    r"^goal-phase-acceptance:sha256:[0-9a-f]{64}$"
)


class GoalPhaseFrontierDependencyGateState(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    HELD = "held"
    SATISFIED = "satisfied"
    STALE = "stale"
    UNRESOLVED = "unresolved"
    REJECTED = "rejected"


class GoalPhaseFrontierEligibility(StrEnum):
    ACCEPTED = "accepted"
    WITHDRAWN = "withdrawn"
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"


def goal_phase_dependency_digest(dependency: GoalPhaseDependency) -> str:
    """Return the semantic digest of one exact Phase dependency."""

    _exact(dependency, GoalPhaseDependency, "dependency")
    return fingerprint(
        {
            "schema_id": "aware.goal.phase-dependency.v1",
            "owner_goal_tag": dependency.owner_goal_tag,
            "dependency_key": dependency.dependency_key,
            "dependent": _coordinate_wire(dependency.dependent),
            "prerequisite": _coordinate_wire(dependency.prerequisite),
            "required_gate_digest": dependency.required_gate_digest,
            "relation": dependency.relation.value,
            "reason": dependency.reason,
            "evidence_refs": list(dependency.evidence_refs),
        }
    )


@dataclass(frozen=True, slots=True)
class GoalPhaseDependencyObservationV2:
    dependency_key: str
    dependency_digest: str
    dependent: GoalPhaseCoordinate
    prerequisite: GoalPhaseCoordinate
    required_gate_digest: str
    relation: GoalDependencyRelation
    outcome: GoalLanePhaseGateOutcome
    dependent_source_revision_ref: str | None
    prerequisite_source_revision_ref: str | None
    prerequisite_phase_state: GoalLanePhaseState | None
    prerequisite_gate_observation_ref: str | None
    prerequisite_acceptance_receipt_ref: str | None
    evidence_refs: tuple[str, ...]
    evaluator_ref: str
    currentness_ref: str
    observation_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_DEPENDENCY_OBSERVATION_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseDependencyObservationV2:
            raise TypeError("observation type must be exact")
        if self.schema_id != GOAL_PHASE_DEPENDENCY_OBSERVATION_SCHEMA:
            raise ValueError("unsupported Phase dependency observation schema")
        object.__setattr__(
            self,
            "dependency_key",
            required_token(self.dependency_key, "dependency_key"),
        )
        object.__setattr__(
            self,
            "dependency_digest",
            _sha256_ref(self.dependency_digest, "dependency_digest"),
        )
        object.__setattr__(
            self,
            "required_gate_digest",
            _sha256_ref(self.required_gate_digest, "required_gate_digest"),
        )
        object.__setattr__(
            self, "evaluator_ref", required_token(self.evaluator_ref, "evaluator_ref")
        )
        object.__setattr__(
            self,
            "currentness_ref",
            required_token(self.currentness_ref, "currentness_ref"),
        )
        _exact(self.dependent, GoalPhaseCoordinate, "dependent")
        _exact(self.prerequisite, GoalPhaseCoordinate, "prerequisite")
        _exact(self.relation, GoalDependencyRelation, "relation")
        _exact(self.outcome, GoalLanePhaseGateOutcome, "outcome")
        if self.outcome is GoalLanePhaseGateOutcome.NOT_EVALUATED:
            raise ValueError("not_evaluated is represented by absent observation")
        object.__setattr__(
            self,
            "dependent_source_revision_ref",
            _optional_token(
                self.dependent_source_revision_ref,
                "dependent_source_revision_ref",
            ),
        )
        object.__setattr__(
            self,
            "prerequisite_source_revision_ref",
            _optional_token(
                self.prerequisite_source_revision_ref,
                "prerequisite_source_revision_ref",
            ),
        )
        object.__setattr__(
            self,
            "prerequisite_gate_observation_ref",
            _optional_token(
                self.prerequisite_gate_observation_ref,
                "prerequisite_gate_observation_ref",
            ),
        )
        object.__setattr__(
            self,
            "prerequisite_acceptance_receipt_ref",
            _optional_token(
                self.prerequisite_acceptance_receipt_ref,
                "prerequisite_acceptance_receipt_ref",
            ),
        )
        if self.prerequisite_phase_state is not None:
            _exact(
                self.prerequisite_phase_state,
                GoalLanePhaseState,
                "prerequisite_phase_state",
            )
        if type(self.evidence_refs) is not tuple:
            raise TypeError("evidence_refs must be exact tuple")
        evidence = tuple(required_token(item, "evidence_ref") for item in self.evidence_refs)
        if evidence != tuple(sorted(set(evidence))):
            raise ValueError("evidence_refs must be unique and sorted")
        object.__setattr__(self, "evidence_refs", evidence)
        unresolved = self.outcome is GoalLanePhaseGateOutcome.UNRESOLVED
        source_values = (
            self.dependent_source_revision_ref,
            self.prerequisite_source_revision_ref,
            self.prerequisite_phase_state,
            self.prerequisite_gate_observation_ref,
            self.prerequisite_acceptance_receipt_ref,
        )
        if unresolved:
            if any(value is not None for value in source_values) or evidence:
                raise ValueError("unresolved observation cannot carry resolved source state")
        else:
            if self.dependent_source_revision_ref is None:
                raise ValueError("evaluated observation requires dependent revision")
            if self.prerequisite_source_revision_ref is None:
                raise ValueError("evaluated observation requires prerequisite revision")
            if self.prerequisite_phase_state is None:
                raise ValueError("evaluated observation requires prerequisite Phase state")
            if self.prerequisite_gate_observation_ref is None:
                raise ValueError("evaluated observation requires Gate observation")
        if self.outcome in (
            GoalLanePhaseGateOutcome.SATISFIED,
            GoalLanePhaseGateOutcome.REJECTED,
        ) and not evidence:
            raise ValueError(f"{self.outcome.value} observation requires evidence")
        if (
            self.outcome is GoalLanePhaseGateOutcome.SATISFIED
            and self.prerequisite_phase_state is GoalLanePhaseState.WITHDRAWN
        ):
            raise ValueError("withdrawn prerequisite cannot satisfy dependency")
        if self.prerequisite_phase_state is GoalLanePhaseState.ACCEPTED:
            if self.prerequisite_acceptance_receipt_ref is None:
                raise ValueError("accepted prerequisite requires acceptance receipt")
            if (
                _ACCEPTANCE_RECEIPT_REF.fullmatch(
                    self.prerequisite_acceptance_receipt_ref
                )
                is None
            ):
                raise ValueError("prerequisite acceptance receipt is not qualified")
        elif self.prerequisite_acceptance_receipt_ref is not None:
            raise ValueError("non-accepted prerequisite cannot carry acceptance receipt")
        if (
            self.relation is GoalDependencyRelation.REQUIRES_ACCEPTANCE
            and self.outcome is GoalLanePhaseGateOutcome.SATISFIED
            and (
                self.prerequisite_phase_state is not GoalLanePhaseState.ACCEPTED
                or self.prerequisite_acceptance_receipt_ref is None
            )
        ):
            raise ValueError("accepted dependency requires accepted Phase receipt")
        expected_ref = "goal-phase-dependency-observation:" + fingerprint(
            {
                "schema_id": self.schema_id,
                "dependency_key": self.dependency_key,
                "dependency_digest": self.dependency_digest,
                "dependent": _coordinate_wire(self.dependent),
                "prerequisite": _coordinate_wire(self.prerequisite),
                "required_gate_digest": self.required_gate_digest,
                "relation": self.relation.value,
                "outcome": self.outcome.value,
                "dependent_source_revision_ref": self.dependent_source_revision_ref,
                "prerequisite_source_revision_ref": (
                    self.prerequisite_source_revision_ref
                ),
                "prerequisite_phase_state": (
                    None
                    if self.prerequisite_phase_state is None
                    else self.prerequisite_phase_state.value
                ),
                "prerequisite_gate_observation_ref": (
                    self.prerequisite_gate_observation_ref
                ),
                "prerequisite_acceptance_receipt_ref": (
                    self.prerequisite_acceptance_receipt_ref
                ),
                "evidence_refs": list(self.evidence_refs),
                "evaluator_ref": self.evaluator_ref,
                "currentness_ref": self.currentness_ref,
            }
        )
        object.__setattr__(self, "observation_ref", expected_ref)

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "observation_ref": self.observation_ref,
            "effect_profile": "read_only_non_authorizing",
            "dependency_key": self.dependency_key,
            "dependency_digest": self.dependency_digest,
            "dependent": _coordinate_wire(self.dependent),
            "prerequisite": _coordinate_wire(self.prerequisite),
            "required_gate_digest": self.required_gate_digest,
            "relation": self.relation.value,
            "outcome": self.outcome.value,
            "dependent_source_revision_ref": self.dependent_source_revision_ref,
            "prerequisite_source_revision_ref": self.prerequisite_source_revision_ref,
            "prerequisite_phase_state": (
                None
                if self.prerequisite_phase_state is None
                else self.prerequisite_phase_state.value
            ),
            "prerequisite_gate_observation_ref": (
                self.prerequisite_gate_observation_ref
            ),
            "prerequisite_acceptance_receipt_ref": (
                self.prerequisite_acceptance_receipt_ref
            ),
            "evidence_refs": list(self.evidence_refs),
            "evaluator_ref": self.evaluator_ref,
            "currentness_ref": self.currentness_ref,
        }


def decode_goal_phase_dependency_observation(
    payload: Mapping[str, object],
    *,
    dependency: GoalPhaseDependency,
) -> GoalPhaseDependencyObservationV2:
    """Strictly decode one observation bound to an exact declaration."""

    _exact(dependency, GoalPhaseDependency, "dependency")
    values = _exact_object(
        payload,
        "Phase dependency observation",
        {
            "schema_id",
            "observation_ref",
            "effect_profile",
            "dependency_key",
            "dependency_digest",
            "dependent",
            "prerequisite",
            "required_gate_digest",
            "relation",
            "outcome",
            "dependent_source_revision_ref",
            "prerequisite_source_revision_ref",
            "prerequisite_phase_state",
            "prerequisite_gate_observation_ref",
            "prerequisite_acceptance_receipt_ref",
            "evidence_refs",
            "evaluator_ref",
            "currentness_ref",
        },
    )
    if _required_string(values["schema_id"], "schema_id") != (
        GOAL_PHASE_DEPENDENCY_OBSERVATION_SCHEMA
    ):
        raise ValueError("unsupported Phase dependency observation schema")
    if _required_string(values["effect_profile"], "effect_profile") != (
        "read_only_non_authorizing"
    ):
        raise ValueError("unsupported observation effect profile")
    state_value = values["prerequisite_phase_state"]
    observation = GoalPhaseDependencyObservationV2(
        dependency_key=_required_string(values["dependency_key"], "dependency_key"),
        dependency_digest=_required_string(
            values["dependency_digest"], "dependency_digest"
        ),
        dependent=_decode_coordinate(values["dependent"], "dependent"),
        prerequisite=_decode_coordinate(values["prerequisite"], "prerequisite"),
        required_gate_digest=_required_string(
            values["required_gate_digest"], "required_gate_digest"
        ),
        relation=GoalDependencyRelation(
            _required_string(values["relation"], "relation")
        ),
        outcome=GoalLanePhaseGateOutcome(
            _required_string(values["outcome"], "outcome")
        ),
        dependent_source_revision_ref=_optional_string(
            values["dependent_source_revision_ref"],
            "dependent_source_revision_ref",
        ),
        prerequisite_source_revision_ref=_optional_string(
            values["prerequisite_source_revision_ref"],
            "prerequisite_source_revision_ref",
        ),
        prerequisite_phase_state=(
            None
            if state_value is None
            else GoalLanePhaseState(
                _required_string(state_value, "prerequisite_phase_state")
            )
        ),
        prerequisite_gate_observation_ref=_optional_string(
            values["prerequisite_gate_observation_ref"],
            "prerequisite_gate_observation_ref",
        ),
        prerequisite_acceptance_receipt_ref=_optional_string(
            values["prerequisite_acceptance_receipt_ref"],
            "prerequisite_acceptance_receipt_ref",
        ),
        evidence_refs=_string_list(values["evidence_refs"], "evidence_refs"),
        evaluator_ref=_required_string(values["evaluator_ref"], "evaluator_ref"),
        currentness_ref=_required_string(
            values["currentness_ref"], "currentness_ref"
        ),
    )
    if _required_string(values["observation_ref"], "observation_ref") != (
        observation.observation_ref
    ):
        raise ValueError("observation_ref differs from canonical observation")
    _validate_observation(dependency, observation)
    return observation


def observe_goal_phase_dependency(
    dependency: GoalPhaseDependency,
    *,
    dependent_source_revision_ref: str,
    prerequisite_source_revision_ref: str,
    prerequisite_phase: GoalLanePhase,
    evaluator_ref: str,
    currentness_ref: str,
) -> GoalPhaseDependencyObservationV2:
    """Observe one resolved prerequisite without inferring from Issue state."""

    _exact(dependency, GoalPhaseDependency, "dependency")
    _exact(prerequisite_phase, GoalLanePhase, "prerequisite_phase")
    if prerequisite_phase.coordinate != dependency.prerequisite:
        raise ValueError("prerequisite Phase coordinate differs from dependency")
    current = tuple(
        observation
        for observation in prerequisite_phase.gate_observations
        if observation.outcome is not GoalLanePhaseGateOutcome.STALE
    )
    if len(current) == 1:
        gate_observation = current[0]
    elif (
        not current
        and len(prerequisite_phase.gate_observations) == 1
        and prerequisite_phase.gate_observations[0].outcome
        is GoalLanePhaseGateOutcome.STALE
    ):
        gate_observation = prerequisite_phase.gate_observations[0]
    else:
        raise ValueError("resolved dependency requires one current Gate observation")
    dependent_source_revision_ref = required_token(
        dependent_source_revision_ref, "dependent_source_revision_ref"
    )
    prerequisite_source_revision_ref = required_token(
        prerequisite_source_revision_ref, "prerequisite_source_revision_ref"
    )
    if prerequisite_source_revision_ref not in gate_observation.source_revision_refs:
        raise ValueError("Gate observation does not bind prerequisite revision")
    outcome = gate_observation.outcome
    if prerequisite_phase.gate.gate_digest != dependency.required_gate_digest:
        outcome = GoalLanePhaseGateOutcome.STALE
    elif (
        outcome is GoalLanePhaseGateOutcome.SATISFIED
        and dependency.relation is GoalDependencyRelation.REQUIRES_ACCEPTANCE
        and prerequisite_phase.state is not GoalLanePhaseState.ACCEPTED
    ):
        outcome = GoalLanePhaseGateOutcome.PENDING
    elif (
        outcome is GoalLanePhaseGateOutcome.SATISFIED
        and prerequisite_phase.state is GoalLanePhaseState.WITHDRAWN
    ):
        raise ValueError("withdrawn prerequisite cannot satisfy dependency")
    return GoalPhaseDependencyObservationV2(
        dependency_key=dependency.dependency_key,
        dependency_digest=goal_phase_dependency_digest(dependency),
        dependent=dependency.dependent,
        prerequisite=dependency.prerequisite,
        required_gate_digest=dependency.required_gate_digest,
        relation=dependency.relation,
        outcome=outcome,
        dependent_source_revision_ref=dependent_source_revision_ref,
        prerequisite_source_revision_ref=prerequisite_source_revision_ref,
        prerequisite_phase_state=prerequisite_phase.state,
        prerequisite_gate_observation_ref=gate_observation.observation_ref,
        prerequisite_acceptance_receipt_ref=(
            prerequisite_phase.last_receipt_ref
            if prerequisite_phase.state is GoalLanePhaseState.ACCEPTED
            else None
        ),
        evidence_refs=gate_observation.evidence_refs,
        evaluator_ref=evaluator_ref,
        currentness_ref=currentness_ref,
    )


def observe_unresolved_goal_phase_dependency(
    dependency: GoalPhaseDependency,
    *,
    evaluator_ref: str,
    currentness_ref: str,
) -> GoalPhaseDependencyObservationV2:
    """Record an explicit unresolved endpoint observation."""

    _exact(dependency, GoalPhaseDependency, "dependency")
    return GoalPhaseDependencyObservationV2(
        dependency_key=dependency.dependency_key,
        dependency_digest=goal_phase_dependency_digest(dependency),
        dependent=dependency.dependent,
        prerequisite=dependency.prerequisite,
        required_gate_digest=dependency.required_gate_digest,
        relation=dependency.relation,
        outcome=GoalLanePhaseGateOutcome.UNRESOLVED,
        dependent_source_revision_ref=None,
        prerequisite_source_revision_ref=None,
        prerequisite_phase_state=None,
        prerequisite_gate_observation_ref=None,
        prerequisite_acceptance_receipt_ref=None,
        evidence_refs=(),
        evaluator_ref=evaluator_ref,
        currentness_ref=currentness_ref,
    )


@dataclass(frozen=True, slots=True)
class GoalPhaseFrontierDependencyGateV2:
    state: GoalPhaseFrontierDependencyGateState
    incoming_count: int
    dependency_keys: tuple[str, ...]
    satisfied_keys: tuple[str, ...]
    pending_keys: tuple[str, ...]
    not_evaluated_keys: tuple[str, ...]
    stale_keys: tuple[str, ...]
    unresolved_keys: tuple[str, ...]
    rejected_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseFrontierDependencyGateV2:
            raise TypeError("dependency gate type must be exact")
        _exact(self.state, GoalPhaseFrontierDependencyGateState, "state")
        if type(self.incoming_count) is not int or self.incoming_count < 0:
            raise ValueError("incoming_count must be nonnegative integer")
        named_values = (
            ("dependency_keys", self.dependency_keys),
            ("satisfied_keys", self.satisfied_keys),
            ("pending_keys", self.pending_keys),
            ("not_evaluated_keys", self.not_evaluated_keys),
            ("stale_keys", self.stale_keys),
            ("unresolved_keys", self.unresolved_keys),
            ("rejected_keys", self.rejected_keys),
        )
        for name, value in named_values:
            if type(value) is not tuple:
                raise TypeError(f"{name} must be exact tuple")
            items = tuple(required_token(item, name) for item in value)
            if items != tuple(sorted(set(items))):
                raise ValueError(f"{name} must be unique and sorted")
        if self.incoming_count != len(self.dependency_keys):
            raise ValueError("incoming_count differs from dependency_keys")
        partitions = (
            self.satisfied_keys,
            self.pending_keys,
            self.not_evaluated_keys,
            self.stale_keys,
            self.unresolved_keys,
            self.rejected_keys,
        )
        flattened = tuple(item for partition in partitions for item in partition)
        if self.state is GoalPhaseFrontierDependencyGateState.NOT_APPLICABLE:
            if flattened:
                raise ValueError("not-applicable gate cannot classify dependencies")
        elif tuple(sorted(flattened)) != self.dependency_keys or len(flattened) != len(
            set(flattened)
        ):
            raise ValueError("dependency state partitions must cover keys exactly")

    def to_wire(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "incoming_count": self.incoming_count,
            "dependency_keys": list(self.dependency_keys),
            "satisfied": list(self.satisfied_keys),
            "pending": list(self.pending_keys),
            "not_evaluated": list(self.not_evaluated_keys),
            "stale": list(self.stale_keys),
            "unresolved": list(self.unresolved_keys),
            "rejected": list(self.rejected_keys),
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseFrontierPhaseProjectionV2:
    phase: GoalLanePhase
    projection_health: GoalFrontierProjectionHealth
    whole_goal_currentness: GoalFrontierCurrentness
    phase_currentness: GoalFrontierCurrentness
    dependency_gate: GoalPhaseFrontierDependencyGateV2
    admission_eligibility: GoalPhaseFrontierEligibility
    suggested_action: str

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseFrontierPhaseProjectionV2:
            raise TypeError("Phase projection type must be exact")
        _exact(self.phase, GoalLanePhase, "phase")
        _exact(self.projection_health, GoalFrontierProjectionHealth, "projection_health")
        _exact(
            self.whole_goal_currentness,
            GoalFrontierCurrentness,
            "whole_goal_currentness",
        )
        _exact(self.phase_currentness, GoalFrontierCurrentness, "phase_currentness")
        _exact(
            self.dependency_gate,
            GoalPhaseFrontierDependencyGateV2,
            "dependency_gate",
        )
        _exact(
            self.admission_eligibility,
            GoalPhaseFrontierEligibility,
            "admission_eligibility",
        )
        object.__setattr__(
            self, "suggested_action", required_token(self.suggested_action, "suggested_action")
        )
        if (
            self.phase.state is GoalLanePhaseState.ACCEPTED
            and self.admission_eligibility is not GoalPhaseFrontierEligibility.ACCEPTED
        ):
            raise ValueError("accepted Phase requires accepted frontier result")
        if (
            self.phase.state is GoalLanePhaseState.WITHDRAWN
            and self.admission_eligibility is not GoalPhaseFrontierEligibility.WITHDRAWN
        ):
            raise ValueError("withdrawn Phase requires withdrawn frontier result")
        if self.phase.state not in (
            GoalLanePhaseState.ACCEPTED,
            GoalLanePhaseState.WITHDRAWN,
        ) and self.admission_eligibility in (
            GoalPhaseFrontierEligibility.ACCEPTED,
            GoalPhaseFrontierEligibility.WITHDRAWN,
        ):
            raise ValueError("unfinished Phase cannot claim terminal frontier result")

    def to_wire(self) -> dict[str, object]:
        return {
            **_coordinate_wire(self.phase.coordinate),
            "ordinal": self.phase.ordinal,
            "phase_state": self.phase.state.value,
            "gate_digest": self.phase.gate.gate_digest,
            "projection_health": self.projection_health.value,
            "whole_goal_currentness": self.whole_goal_currentness.value,
            "phase_currentness": self.phase_currentness.value,
            "dependency_gate": self.dependency_gate.to_wire(),
            "admission_eligibility": self.admission_eligibility.value,
            "suggested_action": self.suggested_action,
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseFrontierLaneProjectionV2:
    lane_key: str
    phases: tuple[GoalPhaseFrontierPhaseProjectionV2, ...]

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseFrontierLaneProjectionV2:
            raise TypeError("lane projection type must be exact")
        object.__setattr__(self, "lane_key", required_token(self.lane_key, "lane_key"))
        if type(self.phases) is not tuple:
            raise TypeError("phases must be exact tuple")
        for phase in self.phases:
            _exact(phase, GoalPhaseFrontierPhaseProjectionV2, "phase")
            if phase.phase.coordinate.lane_key != self.lane_key:
                raise ValueError("Phase projection belongs to another lane")
        ordering = tuple(
            (phase.phase.ordinal, phase.phase.coordinate.phase_key)
            for phase in self.phases
        )
        if ordering != tuple(sorted(ordering)):
            raise ValueError("Phase projections must use presentation order")

    @property
    def default_candidate(self) -> GoalPhaseFrontierPhaseProjectionV2 | None:
        return next(
            (
                phase
                for phase in self.phases
                if phase.admission_eligibility is GoalPhaseFrontierEligibility.ELIGIBLE
            ),
            None,
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "lane_key": self.lane_key,
            "default_candidate_phase_key": (
                None
                if self.default_candidate is None
                else self.default_candidate.phase.coordinate.phase_key
            ),
            "phases": [phase.to_wire() for phase in self.phases],
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseFrontierProjectionV2:
    goal_tag: str
    source_revision_ref: str | None
    whole_goal_currentness: GoalFrontierCurrentness
    lanes: tuple[GoalPhaseFrontierLaneProjectionV2, ...]
    schema_id: str = GOAL_PHASE_FRONTIER_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseFrontierProjectionV2:
            raise TypeError("frontier projection type must be exact")
        if self.schema_id != GOAL_PHASE_FRONTIER_SCHEMA:
            raise ValueError("unsupported Phase frontier schema")
        object.__setattr__(self, "goal_tag", normalize_goal_tag(self.goal_tag))
        object.__setattr__(
            self,
            "source_revision_ref",
            _optional_token(self.source_revision_ref, "source_revision_ref"),
        )
        _exact(
            self.whole_goal_currentness,
            GoalFrontierCurrentness,
            "whole_goal_currentness",
        )
        if type(self.lanes) is not tuple:
            raise TypeError("lanes must be exact tuple")
        lane_keys: list[str] = []
        for lane in self.lanes:
            _exact(lane, GoalPhaseFrontierLaneProjectionV2, "lane")
            lane_keys.append(lane.lane_key)
            if any(
                phase.phase.coordinate.goal_tag != self.goal_tag
                for phase in lane.phases
            ):
                raise ValueError("Phase projection belongs to another Goal")
        if lane_keys != sorted(set(lane_keys)):
            raise ValueError("frontier lanes must be unique and sorted")

    @property
    def eligible(self) -> tuple[GoalPhaseFrontierPhaseProjectionV2, ...]:
        return tuple(
            phase
            for lane in self.lanes
            for phase in lane.phases
            if phase.admission_eligibility is GoalPhaseFrontierEligibility.ELIGIBLE
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "effect_profile": "read_only_non_authorizing",
            "event_effect": "none",
            "ordinal_semantics": "presentation_only",
            "goal_tag": self.goal_tag,
            "source_revision_ref": self.source_revision_ref,
            "whole_goal_currentness": self.whole_goal_currentness.value,
            "lanes": [lane.to_wire() for lane in self.lanes],
            "eligible": [
                _coordinate_wire(phase.phase.coordinate) for phase in self.eligible
            ],
        }


def decode_goal_phase_frontier_projection(
    payload: Mapping[str, object],
    *,
    goal_tag: str,
    source_revision_ref: str | None,
    whole_goal_currentness: GoalFrontierCurrentness,
    bundle: GoalPhaseContractBundleV1,
    observations: Mapping[str, GoalPhaseDependencyObservationV2] | None = None,
    phase_currentness: Mapping[GoalPhaseCoordinate, GoalFrontierCurrentness]
    | None = None,
    lane_projection_health: Mapping[str, GoalFrontierProjectionHealth] | None = None,
    current_revision_by_goal: Mapping[str, str] | None = None,
) -> GoalPhaseFrontierProjectionV2:
    """Decode only the canonical projection for independently supplied inputs."""

    supplied = _strict_json_value(payload, "Phase frontier projection")
    if type(supplied) is not dict:
        raise TypeError("Phase frontier projection must be an exact object")
    supplied_object = cast(dict[str, object], supplied)
    _ = _exact_object(
        supplied_object,
        "Phase frontier projection",
        {
            "schema_id",
            "effect_profile",
            "event_effect",
            "ordinal_semantics",
            "goal_tag",
            "source_revision_ref",
            "whole_goal_currentness",
            "lanes",
            "eligible",
        },
    )
    canonical = project_goal_phase_frontier(
        goal_tag=goal_tag,
        source_revision_ref=source_revision_ref,
        whole_goal_currentness=whole_goal_currentness,
        bundle=bundle,
        observations=observations,
        phase_currentness=phase_currentness,
        lane_projection_health=lane_projection_health,
        current_revision_by_goal=current_revision_by_goal,
    )
    if not _exact_json_equal(supplied_object, canonical.to_wire()):
        raise ValueError("frontier payload differs from canonical projection")
    return canonical


def project_goal_phase_frontier(
    *,
    goal_tag: str,
    source_revision_ref: str | None,
    whole_goal_currentness: GoalFrontierCurrentness,
    bundle: GoalPhaseContractBundleV1,
    observations: Mapping[str, GoalPhaseDependencyObservationV2] | None = None,
    phase_currentness: Mapping[GoalPhaseCoordinate, GoalFrontierCurrentness]
    | None = None,
    lane_projection_health: Mapping[str, GoalFrontierProjectionHealth] | None = None,
    current_revision_by_goal: Mapping[str, str] | None = None,
) -> GoalPhaseFrontierProjectionV2:
    """Project Phase eligibility without treating ordinal as authority."""

    normalized_goal_tag = normalize_goal_tag(goal_tag)
    if source_revision_ref is not None:
        source_revision_ref = required_token(source_revision_ref, "source_revision_ref")
    _exact(whole_goal_currentness, GoalFrontierCurrentness, "whole_goal_currentness")
    _exact(bundle, GoalPhaseContractBundleV1, "bundle")
    phases = {
        phase.coordinate: phase
        for phase in bundle.phases
        if phase.coordinate.goal_tag == normalized_goal_tag
    }
    if len(phases) != len(bundle.phases):
        raise ValueError("frontier bundle contains a Phase from another Goal")
    for dependency in bundle.dependencies:
        if dependency.owner_goal_tag != normalized_goal_tag:
            raise ValueError("frontier dependency belongs to another Goal")
        if dependency.dependent not in phases:
            raise ValueError("dependency dependent Phase is absent")
    dependencies = {item.dependency_key: item for item in bundle.dependencies}
    supplied = {} if observations is None else dict(observations)
    unknown = sorted(set(supplied) - set(dependencies))
    if unknown:
        raise ValueError("observations name undeclared dependencies: " + ",".join(unknown))
    for key, observation in supplied.items():
        _validate_observation(dependencies[key], observation)
    currentness = {} if phase_currentness is None else dict(phase_currentness)
    if any(coordinate not in phases for coordinate in currentness):
        raise ValueError("phase currentness names a Phase outside the Goal")
    health = {} if lane_projection_health is None else dict(lane_projection_health)
    lane_keys = {phase.coordinate.lane_key for phase in phases.values()}
    if set(health) - lane_keys:
        raise ValueError("projection health names an absent lane")
    revisions = {
        normalize_goal_tag(tag): required_token(revision, "current_revision")
        for tag, revision in (current_revision_by_goal or {}).items()
    }
    incoming: dict[GoalPhaseCoordinate, list[GoalPhaseDependency]] = {}
    for dependency in bundle.dependencies:
        incoming.setdefault(dependency.dependent, []).append(dependency)
    lanes: list[GoalPhaseFrontierLaneProjectionV2] = []
    for lane_key in sorted(lane_keys):
        projected = tuple(
            _project_phase(
                phase=phase,
                source_revision_ref=source_revision_ref,
                whole_goal_currentness=whole_goal_currentness,
                phase_currentness=currentness.get(
                    phase.coordinate, GoalFrontierCurrentness.UNKNOWN
                ),
                projection_health=health.get(
                    lane_key, GoalFrontierProjectionHealth.CLEAN
                ),
                dependencies=tuple(incoming.get(phase.coordinate, ())),
                observations=supplied,
                current_revision_by_goal=revisions,
            )
            for phase in sorted(
                (item for item in phases.values() if item.coordinate.lane_key == lane_key),
                key=lambda item: (item.ordinal, item.coordinate.phase_key),
            )
        )
        lanes.append(GoalPhaseFrontierLaneProjectionV2(lane_key, projected))
    return GoalPhaseFrontierProjectionV2(
        goal_tag=normalized_goal_tag,
        source_revision_ref=source_revision_ref,
        whole_goal_currentness=whole_goal_currentness,
        lanes=tuple(lanes),
    )


def _project_phase(
    *,
    phase: GoalLanePhase,
    source_revision_ref: str | None,
    whole_goal_currentness: GoalFrontierCurrentness,
    phase_currentness: GoalFrontierCurrentness,
    projection_health: GoalFrontierProjectionHealth,
    dependencies: tuple[GoalPhaseDependency, ...],
    observations: Mapping[str, GoalPhaseDependencyObservationV2],
    current_revision_by_goal: Mapping[str, str],
) -> GoalPhaseFrontierPhaseProjectionV2:
    if phase.state is GoalLanePhaseState.ACCEPTED:
        eligibility = GoalPhaseFrontierEligibility.ACCEPTED
        gate = _not_applicable_gate(dependencies)
    elif phase.state is GoalLanePhaseState.WITHDRAWN:
        eligibility = GoalPhaseFrontierEligibility.WITHDRAWN
        gate = _not_applicable_gate(dependencies)
    else:
        gate = _dependency_gate(
            dependencies=dependencies,
            observations=observations,
            source_revision_ref=source_revision_ref,
            current_revision_by_goal=current_revision_by_goal,
        )
        eligible = (
            projection_health is GoalFrontierProjectionHealth.CLEAN
            and whole_goal_currentness is GoalFrontierCurrentness.CURRENT
            and phase_currentness is GoalFrontierCurrentness.CURRENT
            and gate.state is GoalPhaseFrontierDependencyGateState.SATISFIED
        )
        eligibility = (
            GoalPhaseFrontierEligibility.ELIGIBLE
            if eligible
            else GoalPhaseFrontierEligibility.INELIGIBLE
        )
    if eligibility is GoalPhaseFrontierEligibility.ELIGIBLE:
        has_current_work = any(
            work.disposition is GoalLanePhaseWorkDisposition.CURRENT
            for work in phase.work_associations
        )
        suggested_action = (
            "inspect_work_association" if has_current_work else "open_issue"
        )
    elif projection_health is GoalFrontierProjectionHealth.AMBIGUOUS:
        suggested_action = "reconcile_goal_projection"
    elif phase.state not in (
        GoalLanePhaseState.ACCEPTED,
        GoalLanePhaseState.WITHDRAWN,
    ) and (
        whole_goal_currentness is not GoalFrontierCurrentness.CURRENT
        or phase_currentness is not GoalFrontierCurrentness.CURRENT
    ):
        suggested_action = "verify_currentness"
    else:
        suggested_action = "none"
    return GoalPhaseFrontierPhaseProjectionV2(
        phase=phase,
        projection_health=projection_health,
        whole_goal_currentness=whole_goal_currentness,
        phase_currentness=phase_currentness,
        dependency_gate=gate,
        admission_eligibility=eligibility,
        suggested_action=suggested_action,
    )


def _dependency_gate(
    *,
    dependencies: tuple[GoalPhaseDependency, ...],
    observations: Mapping[str, GoalPhaseDependencyObservationV2],
    source_revision_ref: str | None,
    current_revision_by_goal: Mapping[str, str],
) -> GoalPhaseFrontierDependencyGateV2:
    states: dict[str, list[str]] = {
        outcome.value: []
        for outcome in GoalLanePhaseGateOutcome
    }
    for dependency in sorted(dependencies, key=lambda item: item.dependency_key):
        observation = observations.get(dependency.dependency_key)
        if observation is None:
            states[GoalLanePhaseGateOutcome.NOT_EVALUATED.value].append(
                dependency.dependency_key
            )
            continue
        outcome = observation.outcome
        if outcome not in (
            GoalLanePhaseGateOutcome.UNRESOLVED,
            GoalLanePhaseGateOutcome.STALE,
        ):
            dependent_revision = current_revision_by_goal.get(
                dependency.dependent.goal_tag
            )
            prerequisite_revision = current_revision_by_goal.get(
                dependency.prerequisite.goal_tag
            )
            if (
                source_revision_ref is None
                or dependent_revision != source_revision_ref
                or observation.dependent_source_revision_ref != dependent_revision
                or prerequisite_revision is None
                or observation.prerequisite_source_revision_ref
                != prerequisite_revision
            ):
                outcome = GoalLanePhaseGateOutcome.STALE
        states[outcome.value].append(dependency.dependency_key)
    if states[GoalLanePhaseGateOutcome.REJECTED.value]:
        gate_state = GoalPhaseFrontierDependencyGateState.REJECTED
    elif states[GoalLanePhaseGateOutcome.UNRESOLVED.value]:
        gate_state = GoalPhaseFrontierDependencyGateState.UNRESOLVED
    elif states[GoalLanePhaseGateOutcome.STALE.value]:
        gate_state = GoalPhaseFrontierDependencyGateState.STALE
    elif (
        states[GoalLanePhaseGateOutcome.NOT_EVALUATED.value]
        or states[GoalLanePhaseGateOutcome.PENDING.value]
    ):
        gate_state = GoalPhaseFrontierDependencyGateState.HELD
    else:
        gate_state = GoalPhaseFrontierDependencyGateState.SATISFIED
    return GoalPhaseFrontierDependencyGateV2(
        state=gate_state,
        incoming_count=len(dependencies),
        dependency_keys=tuple(
            sorted(dependency.dependency_key for dependency in dependencies)
        ),
        satisfied_keys=tuple(states[GoalLanePhaseGateOutcome.SATISFIED.value]),
        pending_keys=tuple(states[GoalLanePhaseGateOutcome.PENDING.value]),
        not_evaluated_keys=tuple(
            states[GoalLanePhaseGateOutcome.NOT_EVALUATED.value]
        ),
        stale_keys=tuple(states[GoalLanePhaseGateOutcome.STALE.value]),
        unresolved_keys=tuple(states[GoalLanePhaseGateOutcome.UNRESOLVED.value]),
        rejected_keys=tuple(states[GoalLanePhaseGateOutcome.REJECTED.value]),
    )


def _not_applicable_gate(
    dependencies: tuple[GoalPhaseDependency, ...],
) -> GoalPhaseFrontierDependencyGateV2:
    return GoalPhaseFrontierDependencyGateV2(
        state=GoalPhaseFrontierDependencyGateState.NOT_APPLICABLE,
        incoming_count=len(dependencies),
        dependency_keys=tuple(
            sorted(dependency.dependency_key for dependency in dependencies)
        ),
        satisfied_keys=(),
        pending_keys=(),
        not_evaluated_keys=(),
        stale_keys=(),
        unresolved_keys=(),
        rejected_keys=(),
    )


def _validate_observation(
    dependency: GoalPhaseDependency,
    observation: GoalPhaseDependencyObservationV2,
) -> None:
    _exact(observation, GoalPhaseDependencyObservationV2, "observation")
    expected = (
        dependency.dependency_key,
        goal_phase_dependency_digest(dependency),
        dependency.dependent,
        dependency.prerequisite,
        dependency.required_gate_digest,
        dependency.relation,
    )
    actual = (
        observation.dependency_key,
        observation.dependency_digest,
        observation.dependent,
        observation.prerequisite,
        observation.required_gate_digest,
        observation.relation,
    )
    if actual != expected:
        raise ValueError("observation differs from exact Phase dependency")


def _coordinate_wire(coordinate: GoalPhaseCoordinate) -> dict[str, str]:
    return {
        "goal_tag": coordinate.goal_tag,
        "lane_key": coordinate.lane_key,
        "phase_key": coordinate.phase_key,
    }


def _exact(value: object, expected: type[object], field_name: str) -> None:
    if type(value) is not expected:
        raise TypeError(f"{field_name} must be exact {expected.__name__}")


def _optional_token(value: str | None, field_name: str) -> str | None:
    return None if value is None else required_token(value, field_name)


def _sha256_ref(value: str, field_name: str) -> str:
    value = required_token(value, field_name)
    if _SHA256_REF.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be exact lowercase SHA-256 ref")
    return value


def _required_string(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exact string")
    return value


def _optional_string(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _required_string(value, field_name)


def _string_list(value: object, field_name: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise TypeError(f"{field_name} must be exact list")
    items = cast(list[object], value)
    return tuple(_required_string(item, field_name) for item in items)


def _decode_coordinate(value: object, field_name: str) -> GoalPhaseCoordinate:
    values = _exact_object(
        value,
        field_name,
        {"goal_tag", "lane_key", "phase_key"},
    )
    return GoalPhaseCoordinate(
        goal_tag=_required_string(values["goal_tag"], f"{field_name}.goal_tag"),
        lane_key=_required_string(values["lane_key"], f"{field_name}.lane_key"),
        phase_key=_required_string(values["phase_key"], f"{field_name}.phase_key"),
    )


def _exact_object(
    value: object,
    field_name: str,
    expected_fields: set[str],
) -> dict[str, object]:
    if type(value) is not dict:
        raise TypeError(f"{field_name} must be an exact object")
    raw = cast(dict[object, object], value)
    if not all(type(key) is str for key in raw):
        raise TypeError(f"{field_name} keys must be exact strings")
    result = {cast(str, key): item for key, item in raw.items()}
    actual_fields = set(result)
    if actual_fields != expected_fields:
        missing = sorted(expected_fields - actual_fields)
        unknown = sorted(actual_fields - expected_fields)
        raise ValueError(
            f"{field_name} fields differ; missing={missing}, unknown={unknown}"
        )
    return result


def _strict_json_value(value: object, field_name: str) -> object:
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is list:
        items = cast(list[object], value)
        return [
            _strict_json_value(item, f"{field_name}[]")
            for item in items
        ]
    if type(value) is dict:
        raw = cast(dict[object, object], value)
        if not all(type(key) is str for key in raw):
            raise TypeError(f"{field_name} keys must be exact strings")
        return {
            cast(str, key): _strict_json_value(item, f"{field_name}.{key}")
            for key, item in raw.items()
        }
    raise TypeError(f"{field_name} contains a non-JSON value")


def _exact_json_equal(left: object, right: object) -> bool:
    """Compare JSON trees without Python's bool/int value coercion."""

    if type(left) is not type(right):
        return False
    if type(left) is list:
        left_items = cast(list[object], left)
        right_items = cast(list[object], right)
        return len(left_items) == len(right_items) and all(
            _exact_json_equal(left_item, right_item)
            for left_item, right_item in zip(left_items, right_items, strict=True)
        )
    if type(left) is dict:
        left_object = cast(dict[str, object], left)
        right_object = cast(dict[str, object], right)
        return set(left_object) == set(right_object) and all(
            _exact_json_equal(left_object[key], right_object[key])
            for key in left_object
        )
    return left == right
