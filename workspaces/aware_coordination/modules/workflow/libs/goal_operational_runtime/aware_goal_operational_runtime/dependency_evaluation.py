"""Evidence-qualified GoalDependency observations.

This module evaluates explicit inputs only. It does not infer dependency edges,
derive evidence from Issue closure or row state, mutate Goal authority, or grant
permission to pursue, dispatch, or perform work.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .dependencies import (
    GoalDependency,
    GoalDependencyRelation,
    GoalRowCoordinate,
)
from .identity import (
    fingerprint,
    normalize_goal_tag,
    optional_token,
    required_token,
    stable_ref,
    unique_tokens,
)


class GoalRowResolutionOutcome(StrEnum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"


class GoalDependencyEvidenceKind(StrEnum):
    COMPLETION = "completion"
    ACCEPTANCE = "acceptance"


class GoalDependencySatisfaction(StrEnum):
    SATISFIED = "satisfied"
    PENDING = "pending"
    STALE = "stale"
    UNRESOLVED = "unresolved"


class GoalDependencyGateState(StrEnum):
    CLEAR = "clear"
    BLOCKED = "blocked"
    STALE = "stale"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class GoalRowSourceObservation:
    coordinate: GoalRowCoordinate
    outcome: GoalRowResolutionOutcome
    source_revision_ref: str | None = None
    gate_digest: str | None = None
    candidate_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.coordinate, GoalRowCoordinate):
            raise TypeError("coordinate must be GoalRowCoordinate")
        if not isinstance(self.outcome, GoalRowResolutionOutcome):
            raise TypeError("outcome must be GoalRowResolutionOutcome")
        object.__setattr__(
            self,
            "source_revision_ref",
            optional_token(self.source_revision_ref, "source_revision_ref"),
        )
        object.__setattr__(
            self,
            "gate_digest",
            optional_token(self.gate_digest, "gate_digest"),
        )
        if not isinstance(self.candidate_refs, tuple):
            raise TypeError("candidate_refs must be a tuple")
        object.__setattr__(
            self,
            "candidate_refs",
            unique_tokens(self.candidate_refs, "candidate_refs"),
        )
        if self.outcome is GoalRowResolutionOutcome.RESOLVED:
            if self.source_revision_ref is None:
                raise ValueError("resolved row observation requires source revision")
            if self.candidate_refs:
                raise ValueError("resolved row observation cannot carry candidates")
        elif self.outcome is GoalRowResolutionOutcome.UNRESOLVED:
            if any(
                value is not None
                for value in (self.source_revision_ref, self.gate_digest)
            ) or self.candidate_refs:
                raise ValueError("unresolved row observation cannot carry source state")
        elif self.source_revision_ref is not None or self.gate_digest is not None:
            raise ValueError("ambiguous row observation cannot carry source state")
        elif len(self.candidate_refs) < 2:
            raise ValueError("ambiguous row observation requires multiple candidates")

    def to_wire(self) -> dict[str, object]:
        return {
            "coordinate": _coordinate_wire(self.coordinate),
            "outcome": self.outcome.value,
            "source_revision_ref": self.source_revision_ref,
            "gate_digest": self.gate_digest,
            "candidate_refs": list(self.candidate_refs),
        }


@dataclass(frozen=True, slots=True)
class GoalDependencyEvidence:
    owner_goal_tag: str
    dependency_key: str
    dependency_digest: str
    prerequisite: GoalRowCoordinate
    dependent_source_revision_ref: str
    prerequisite_source_revision_ref: str
    prerequisite_gate_digest: str
    kind: GoalDependencyEvidenceKind
    evidence_ref: str
    qualification_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "owner_goal_tag",
            normalize_goal_tag(self.owner_goal_tag),
        )
        for field in (
            "dependency_key",
            "dependency_digest",
            "dependent_source_revision_ref",
            "prerequisite_source_revision_ref",
            "prerequisite_gate_digest",
            "evidence_ref",
            "qualification_ref",
        ):
            object.__setattr__(
                self,
                field,
                required_token(getattr(self, field), field),
            )
        if not isinstance(self.prerequisite, GoalRowCoordinate):
            raise TypeError("prerequisite must be GoalRowCoordinate")
        if not isinstance(self.kind, GoalDependencyEvidenceKind):
            raise TypeError("kind must be GoalDependencyEvidenceKind")

    def to_wire(self) -> dict[str, object]:
        return {
            "owner_goal_tag": self.owner_goal_tag,
            "dependency_key": self.dependency_key,
            "dependency_digest": self.dependency_digest,
            "prerequisite": _coordinate_wire(self.prerequisite),
            "dependent_source_revision_ref": self.dependent_source_revision_ref,
            "prerequisite_source_revision_ref": (
                self.prerequisite_source_revision_ref
            ),
            "prerequisite_gate_digest": self.prerequisite_gate_digest,
            "kind": self.kind.value,
            "evidence_ref": self.evidence_ref,
            "qualification_ref": self.qualification_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalDependencyObservation:
    schema_id: str
    observation_ref: str
    effect_profile: str
    evaluator_ref: str
    owner_goal_tag: str
    dependency_key: str
    dependency_digest: str
    relation: GoalDependencyRelation
    dependent: GoalRowCoordinate
    prerequisite: GoalRowCoordinate
    dependent_source_revision_ref: str | None
    prerequisite_source_revision_ref: str | None
    prerequisite_gate_digest: str | None
    satisfaction: GoalDependencySatisfaction
    evidence_refs: tuple[str, ...]
    qualification_refs: tuple[str, ...]
    reasons: tuple[str, ...]

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "observation_ref": self.observation_ref,
            "effect_profile": self.effect_profile,
            "evaluator_ref": self.evaluator_ref,
            "owner_goal_tag": self.owner_goal_tag,
            "dependency_key": self.dependency_key,
            "dependency_digest": self.dependency_digest,
            "relation": self.relation.value,
            "dependent": _coordinate_wire(self.dependent),
            "prerequisite": _coordinate_wire(self.prerequisite),
            "dependent_source_revision_ref": self.dependent_source_revision_ref,
            "prerequisite_source_revision_ref": (
                self.prerequisite_source_revision_ref
            ),
            "prerequisite_gate_digest": self.prerequisite_gate_digest,
            "satisfaction": self.satisfaction.value,
            "evidence_refs": list(self.evidence_refs),
            "qualification_refs": list(self.qualification_refs),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True, slots=True)
class GoalDependencyGateObservation:
    schema_id: str
    gate_ref: str
    effect_profile: str
    evaluator_ref: str
    dependent: GoalRowCoordinate
    state: GoalDependencyGateState
    dependency_observation_refs: tuple[str, ...]
    blocking_dependency_keys: tuple[str, ...]
    reasons: tuple[str, ...]

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "gate_ref": self.gate_ref,
            "effect_profile": self.effect_profile,
            "evaluator_ref": self.evaluator_ref,
            "dependent": _coordinate_wire(self.dependent),
            "state": self.state.value,
            "dependency_observation_refs": list(
                self.dependency_observation_refs
            ),
            "blocking_dependency_keys": list(self.blocking_dependency_keys),
            "reasons": list(self.reasons),
        }


def dependency_definition_digest(dependency: GoalDependency) -> str:
    if not isinstance(dependency, GoalDependency):
        raise TypeError("dependency must be GoalDependency")
    return fingerprint(dependency.to_wire())


def evaluate_goal_dependency(
    dependency: GoalDependency,
    *,
    dependent: GoalRowSourceObservation,
    prerequisite: GoalRowSourceObservation,
    evidence: tuple[GoalDependencyEvidence, ...] = (),
    evaluator_ref: str,
) -> GoalDependencyObservation:
    """Evaluate one declaration against explicit source and evidence inputs."""

    if not isinstance(dependency, GoalDependency):
        raise TypeError("dependency must be GoalDependency")
    if not isinstance(dependent, GoalRowSourceObservation):
        raise TypeError("dependent must be GoalRowSourceObservation")
    if not isinstance(prerequisite, GoalRowSourceObservation):
        raise TypeError("prerequisite must be GoalRowSourceObservation")
    if dependent.coordinate != dependency.dependent:
        raise ValueError("dependent observation coordinate differs from declaration")
    if prerequisite.coordinate != dependency.prerequisite:
        raise ValueError("prerequisite observation coordinate differs from declaration")
    if not isinstance(evidence, tuple) or not all(
        isinstance(item, GoalDependencyEvidence) for item in evidence
    ):
        raise TypeError("evidence must be a tuple of GoalDependencyEvidence")
    evaluator_ref = required_token(evaluator_ref, "evaluator_ref")
    definition_digest = dependency_definition_digest(dependency)

    reasons = _resolution_reasons(
        dependent=dependent,
        prerequisite=prerequisite,
    )
    considered: tuple[GoalDependencyEvidence, ...] = ()
    if reasons:
        satisfaction = GoalDependencySatisfaction.UNRESOLVED
    else:
        required_kind = _required_evidence_kind(dependency.relation)
        considered = tuple(
            item
            for item in evidence
            if item.owner_goal_tag == dependency.owner_goal_tag
            and item.dependency_key == dependency.dependency_key
            and item.kind is required_kind
        )
        current = tuple(
            item
            for item in considered
            if not _evidence_drift_reasons(
                evidence=item,
                dependency=dependency,
                definition_digest=definition_digest,
                dependent=dependent,
                prerequisite=prerequisite,
            )
        )
        if current:
            satisfaction = GoalDependencySatisfaction.SATISFIED
            considered = current
            reasons = ()
        elif considered:
            satisfaction = GoalDependencySatisfaction.STALE
            reasons = tuple(
                dict.fromkeys(
                    reason
                    for item in considered
                    for reason in _evidence_drift_reasons(
                        evidence=item,
                        dependency=dependency,
                        definition_digest=definition_digest,
                        dependent=dependent,
                        prerequisite=prerequisite,
                    )
                )
            )
        else:
            satisfaction = GoalDependencySatisfaction.PENDING
            reasons = (f"{required_kind.value}_evidence_missing",)

    considered = tuple(sorted(considered, key=lambda item: item.evidence_ref))
    evidence_refs = tuple(item.evidence_ref for item in considered)
    qualification_refs = tuple(
        dict.fromkeys(item.qualification_ref for item in considered)
    )
    observation_ref = stable_ref(
        kind="goal-dependency-observation",
        authority_ref=evaluator_ref,
        coordinates=(
            dependency.owner_goal_tag,
            dependency.dependency_key,
            definition_digest,
            satisfaction.value,
            dependent.source_revision_ref or "none",
            prerequisite.source_revision_ref or "none",
            prerequisite.gate_digest or "none",
            *evidence_refs,
            *qualification_refs,
            *reasons,
        ),
    )
    return GoalDependencyObservation(
        schema_id="aware.goal.dependency.observation.v0",
        observation_ref=observation_ref,
        effect_profile="read_only_non_authorizing",
        evaluator_ref=evaluator_ref,
        owner_goal_tag=dependency.owner_goal_tag,
        dependency_key=dependency.dependency_key,
        dependency_digest=definition_digest,
        relation=dependency.relation,
        dependent=dependency.dependent,
        prerequisite=dependency.prerequisite,
        dependent_source_revision_ref=dependent.source_revision_ref,
        prerequisite_source_revision_ref=prerequisite.source_revision_ref,
        prerequisite_gate_digest=prerequisite.gate_digest,
        satisfaction=satisfaction,
        evidence_refs=evidence_refs,
        qualification_refs=qualification_refs,
        reasons=reasons,
    )


def summarize_goal_dependency_gate(
    dependent: GoalRowCoordinate,
    observations: tuple[GoalDependencyObservation, ...],
    *,
    evaluator_ref: str,
) -> GoalDependencyGateObservation:
    """Summarize conjunctive dependencies without granting work authority."""

    if not isinstance(dependent, GoalRowCoordinate):
        raise TypeError("dependent must be GoalRowCoordinate")
    if not isinstance(observations, tuple) or not all(
        isinstance(item, GoalDependencyObservation) for item in observations
    ):
        raise TypeError("observations must be a tuple of GoalDependencyObservation")
    evaluator_ref = required_token(evaluator_ref, "evaluator_ref")
    identities: set[tuple[str, str]] = set()
    for observation in observations:
        if observation.dependent != dependent:
            raise ValueError("dependency observation belongs to another dependent row")
        identity = (observation.owner_goal_tag, observation.dependency_key)
        if identity in identities:
            raise ValueError("duplicate dependency observation identity")
        identities.add(identity)

    satisfactions = {item.satisfaction for item in observations}
    if GoalDependencySatisfaction.STALE in satisfactions:
        state = GoalDependencyGateState.STALE
    elif GoalDependencySatisfaction.UNRESOLVED in satisfactions:
        state = GoalDependencyGateState.UNRESOLVED
    elif GoalDependencySatisfaction.PENDING in satisfactions:
        state = GoalDependencyGateState.BLOCKED
    else:
        state = GoalDependencyGateState.CLEAR

    ordered = tuple(
        sorted(
            observations,
            key=lambda item: (item.owner_goal_tag, item.dependency_key),
        )
    )
    observation_refs = tuple(item.observation_ref for item in ordered)
    blocking_keys = tuple(
        item.dependency_key
        for item in ordered
        if item.satisfaction is not GoalDependencySatisfaction.SATISFIED
    )
    reasons = (
        ("no_declared_dependencies",)
        if not ordered
        else tuple(
            f"{item.dependency_key}:{item.satisfaction.value}"
            for item in ordered
            if item.satisfaction is not GoalDependencySatisfaction.SATISFIED
        )
    )
    gate_ref = stable_ref(
        kind="goal-dependency-gate",
        authority_ref=evaluator_ref,
        coordinates=(
            dependent.goal_tag,
            dependent.lane_key,
            dependent.row_key,
            state.value,
            *(observation_refs or ("none",)),
        ),
    )
    return GoalDependencyGateObservation(
        schema_id="aware.goal.dependency.gate.v0",
        gate_ref=gate_ref,
        effect_profile="read_only_non_authorizing",
        evaluator_ref=evaluator_ref,
        dependent=dependent,
        state=state,
        dependency_observation_refs=observation_refs,
        blocking_dependency_keys=blocking_keys,
        reasons=reasons,
    )


def _resolution_reasons(
    *,
    dependent: GoalRowSourceObservation,
    prerequisite: GoalRowSourceObservation,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if dependent.outcome is not GoalRowResolutionOutcome.RESOLVED:
        reasons.append(f"dependent_{dependent.outcome.value}")
    if prerequisite.outcome is not GoalRowResolutionOutcome.RESOLVED:
        reasons.append(f"prerequisite_{prerequisite.outcome.value}")
    elif prerequisite.gate_digest is None:
        reasons.append("prerequisite_gate_digest_missing")
    return tuple(reasons)


def _required_evidence_kind(
    relation: GoalDependencyRelation,
) -> GoalDependencyEvidenceKind:
    return {
        GoalDependencyRelation.REQUIRES_COMPLETION: (
            GoalDependencyEvidenceKind.COMPLETION
        ),
        GoalDependencyRelation.REQUIRES_ACCEPTANCE: (
            GoalDependencyEvidenceKind.ACCEPTANCE
        ),
    }[relation]


def _evidence_drift_reasons(
    *,
    evidence: GoalDependencyEvidence,
    dependency: GoalDependency,
    definition_digest: str,
    dependent: GoalRowSourceObservation,
    prerequisite: GoalRowSourceObservation,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if evidence.dependency_digest != definition_digest:
        reasons.append("dependency_definition_changed")
    if evidence.prerequisite != dependency.prerequisite:
        reasons.append("prerequisite_coordinate_changed")
    if evidence.dependent_source_revision_ref != dependent.source_revision_ref:
        reasons.append("dependent_source_revision_changed")
    if evidence.prerequisite_source_revision_ref != prerequisite.source_revision_ref:
        reasons.append("prerequisite_source_revision_changed")
    if evidence.prerequisite_gate_digest != prerequisite.gate_digest:
        reasons.append("prerequisite_gate_changed")
    return tuple(reasons)


def _coordinate_wire(coordinate: GoalRowCoordinate) -> dict[str, str]:
    return {
        "goal_tag": coordinate.goal_tag,
        "lane_key": coordinate.lane_key,
        "row_key": coordinate.row_key,
    }


__all__ = [
    "GoalDependencyEvidence",
    "GoalDependencyEvidenceKind",
    "GoalDependencyGateObservation",
    "GoalDependencyGateState",
    "GoalDependencyObservation",
    "GoalDependencySatisfaction",
    "GoalRowResolutionOutcome",
    "GoalRowSourceObservation",
    "dependency_definition_digest",
    "evaluate_goal_dependency",
    "summarize_goal_dependency_gate",
]
