"""Portable Goal Lane Phase/Gate contracts.

These values describe authored milestone meaning and evaluator-owned evidence.
They do not parse Markdown, mutate a Goal, infer Issue lifecycle, accept a
Phase, calculate a frontier, or authorize execution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import cast

from .dependencies import GoalDependencyRelation
from .identity import fingerprint, normalize_goal_tag, required_text

GOAL_PHASE_GATE_CONTRACT = "aware.goal.lane-phase-gate.v1"
GOAL_PHASE_BUNDLE_SCHEMA = "aware.goal.lane-phase.bundle.v1"

_MEMBER_KEY = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")
_ACCEPTANCE_RECEIPT_REF = re.compile(r"^goal-phase-acceptance:sha256:[0-9a-f]{64}$")
_UTC_INSTANT = re.compile(
    r"^(?P<year>[0-9]{4})-(?P<month>0[1-9]|1[0-2])-(?P<day>0[1-9]|[12][0-9]|3[01])"
    + r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z$"
)


class GoalPhaseContractError(ValueError):
    """A portable Phase/Gate value violates the v1 contract."""


class GoalLanePhaseState(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    HELD = "held"
    ACCEPTED = "accepted"
    WITHDRAWN = "withdrawn"


class GoalLanePhaseGateOutcome(StrEnum):
    NOT_EVALUATED = "not_evaluated"
    PENDING = "pending"
    SATISFIED = "satisfied"
    STALE = "stale"
    UNRESOLVED = "unresolved"
    REJECTED = "rejected"


class GoalLanePhaseWorkRole(StrEnum):
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    ACCEPTANCE = "acceptance"
    CORRECTION = "correction"
    GOVERNANCE = "governance"


class GoalLanePhaseWorkDisposition(StrEnum):
    CURRENT = "current"
    RETIRED = "retired"


def _exact_type(value: object, expected: type[object], field_name: str) -> None:
    if type(value) is not expected:
        raise TypeError(f"{field_name} must be exact {expected.__name__}")


def _text(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exact str")
    normalized = required_text(value, field_name)
    if normalized != value:
        raise GoalPhaseContractError(f"{field_name} must be canonical text")
    return normalized


def _goal_tag(value: object, field_name: str = "goal_tag") -> str:
    return normalize_goal_tag(_text(value, field_name))


def _optional_text(value: object | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _text(value, field_name)


def _member_key(value: object, field_name: str) -> str:
    value = _text(value, field_name)
    if not _MEMBER_KEY.fullmatch(value):
        raise GoalPhaseContractError(f"{field_name} must be lowercase ASCII kebab case")
    if len(value.encode("utf-8")) > 96:
        raise GoalPhaseContractError(f"{field_name} exceeds 96 UTF-8 bytes")
    return value


def _token(value: object, field_name: str) -> str:
    value = _text(value, field_name)
    if any(character.isspace() for character in value) or "|" in value:
        raise GoalPhaseContractError(f"{field_name} must be one portable token")
    return value


def _sha256_ref(value: object, field_name: str) -> str:
    value = _token(value, field_name)
    if not _SHA256_REF.fullmatch(value):
        raise GoalPhaseContractError(
            f"{field_name} must be an exact lowercase SHA-256 ref"
        )
    return value


def _positive_int(value: object, field_name: str) -> int:
    if type(value) is not int or value < 1:
        raise GoalPhaseContractError(f"{field_name} must be a positive integer")
    return value


def _nonnegative_int(value: object, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise GoalPhaseContractError(f"{field_name} must be nonnegative")
    return value


def _sorted_tokens(values: object, field_name: str) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError(f"{field_name} must be an exact tuple")
    items = cast(tuple[object, ...], values)
    normalized = tuple(_token(item, field_name) for item in items)
    if normalized != tuple(sorted(set(normalized))):
        raise GoalPhaseContractError(f"{field_name} must be unique and sorted")
    return normalized


def _utc_instant(value: object, field_name: str) -> str:
    value = _text(value, field_name)
    matched = _UTC_INSTANT.fullmatch(value)
    if matched is None:
        raise GoalPhaseContractError(f"{field_name} must be canonical ISO-8601 UTC")
    year = int(matched.group("year"))
    month = int(matched.group("month"))
    day = int(matched.group("day"))
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    month_days = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if day > month_days[month - 1]:
        raise GoalPhaseContractError(f"{field_name} must be a real UTC calendar date")
    return value


@dataclass(frozen=True, slots=True)
class GoalPhaseCoordinate:
    goal_tag: str
    lane_key: str
    phase_key: str

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseCoordinate:
            raise GoalPhaseContractError("coordinate type must be exact")
        object.__setattr__(self, "goal_tag", _goal_tag(self.goal_tag))
        object.__setattr__(self, "lane_key", _member_key(self.lane_key, "lane_key"))
        object.__setattr__(self, "phase_key", _member_key(self.phase_key, "phase_key"))


@dataclass(frozen=True, slots=True)
class GoalLanePhaseGate:
    gate_key: str
    promise: str
    gate_contract_ref: str
    evidence_schema_ref: str
    invariant_refs: tuple[str, ...] = ()
    semantic_revision: int = 1
    gate_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not GoalLanePhaseGate:
            raise GoalPhaseContractError("gate type must be exact")
        object.__setattr__(self, "gate_key", _member_key(self.gate_key, "gate_key"))
        object.__setattr__(self, "promise", _text(self.promise, "promise"))
        object.__setattr__(
            self,
            "gate_contract_ref",
            _token(self.gate_contract_ref, "gate_contract_ref"),
        )
        object.__setattr__(
            self,
            "evidence_schema_ref",
            _token(self.evidence_schema_ref, "evidence_schema_ref"),
        )
        object.__setattr__(
            self,
            "invariant_refs",
            _sorted_tokens(self.invariant_refs, "invariant_refs"),
        )
        object.__setattr__(
            self,
            "semantic_revision",
            _positive_int(self.semantic_revision, "semantic_revision"),
        )
        object.__setattr__(
            self,
            "gate_digest",
            fingerprint(
                {
                    "contract": GOAL_PHASE_GATE_CONTRACT,
                    "gate": self.semantic_body(),
                }
            ),
        )

    def semantic_body(self) -> dict[str, object]:
        return {
            "gate_key": self.gate_key,
            "promise": self.promise,
            "gate_contract_ref": self.gate_contract_ref,
            "evidence_schema_ref": self.evidence_schema_ref,
            "invariant_refs": list(self.invariant_refs),
            "semantic_revision": self.semantic_revision,
        }


@dataclass(frozen=True, slots=True)
class GoalLanePhaseGateObservation:
    observation_ref: str
    gate_digest: str
    outcome: GoalLanePhaseGateOutcome
    evaluator_ref: str
    evidence_refs: tuple[str, ...]
    source_revision_refs: tuple[str, ...]
    evaluated_at: str
    currentness_ref: str

    def __post_init__(self) -> None:
        if type(self) is not GoalLanePhaseGateObservation:
            raise GoalPhaseContractError("gate observation type must be exact")
        object.__setattr__(
            self, "observation_ref", _token(self.observation_ref, "observation_ref")
        )
        object.__setattr__(
            self, "gate_digest", _sha256_ref(self.gate_digest, "gate_digest")
        )
        _exact_type(self.outcome, GoalLanePhaseGateOutcome, "outcome")
        if self.outcome is GoalLanePhaseGateOutcome.NOT_EVALUATED:
            raise GoalPhaseContractError(
                "not_evaluated is represented by absence of an observation"
            )
        object.__setattr__(
            self, "evaluator_ref", _token(self.evaluator_ref, "evaluator_ref")
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _sorted_tokens(self.evidence_refs, "evidence_refs"),
        )
        object.__setattr__(
            self,
            "source_revision_refs",
            _sorted_tokens(self.source_revision_refs, "source_revision_refs"),
        )
        object.__setattr__(
            self, "evaluated_at", _utc_instant(self.evaluated_at, "evaluated_at")
        )
        object.__setattr__(
            self,
            "currentness_ref",
            _token(self.currentness_ref, "currentness_ref"),
        )
        if not self.source_revision_refs:
            raise GoalPhaseContractError("gate observation requires source revisions")
        if (
            self.outcome
            in (
                GoalLanePhaseGateOutcome.SATISFIED,
                GoalLanePhaseGateOutcome.REJECTED,
            )
            and not self.evidence_refs
        ):
            raise GoalPhaseContractError(
                f"{self.outcome.value} observation requires evidence"
            )


@dataclass(frozen=True, slots=True)
class GoalLanePhaseWork:
    association_ref: str
    issue_ref: str
    role: GoalLanePhaseWorkRole
    disposition: GoalLanePhaseWorkDisposition
    admitted_at: str
    receipt_ref: str
    retired_at: str | None = None

    def __post_init__(self) -> None:
        if type(self) is not GoalLanePhaseWork:
            raise GoalPhaseContractError("phase work type must be exact")
        object.__setattr__(
            self, "association_ref", _token(self.association_ref, "association_ref")
        )
        object.__setattr__(self, "issue_ref", _token(self.issue_ref, "issue_ref"))
        _exact_type(self.role, GoalLanePhaseWorkRole, "role")
        _exact_type(self.disposition, GoalLanePhaseWorkDisposition, "disposition")
        object.__setattr__(
            self, "admitted_at", _utc_instant(self.admitted_at, "admitted_at")
        )
        object.__setattr__(self, "receipt_ref", _token(self.receipt_ref, "receipt_ref"))
        retired_at = (
            None
            if self.retired_at is None
            else _utc_instant(self.retired_at, "retired_at")
        )
        object.__setattr__(self, "retired_at", retired_at)
        if self.disposition is GoalLanePhaseWorkDisposition.CURRENT and retired_at:
            raise GoalPhaseContractError("current work cannot carry retired_at")
        if self.disposition is GoalLanePhaseWorkDisposition.RETIRED and not retired_at:
            raise GoalPhaseContractError("retired work requires retired_at")
        if retired_at is not None and retired_at < self.admitted_at:
            raise GoalPhaseContractError("retired_at cannot precede admitted_at")


@dataclass(frozen=True, slots=True)
class GoalLanePhase:
    coordinate: GoalPhaseCoordinate
    title: str
    ordinal: int
    intent: str
    state: GoalLanePhaseState
    gate: GoalLanePhaseGate
    gate_observations: tuple[GoalLanePhaseGateObservation, ...] = ()
    work_associations: tuple[GoalLanePhaseWork, ...] = ()
    pursuit_directive: str | None = None
    last_receipt_ref: str | None = None

    def __post_init__(self) -> None:
        if type(self) is not GoalLanePhase:
            raise GoalPhaseContractError("phase type must be exact")
        _exact_type(self.coordinate, GoalPhaseCoordinate, "coordinate")
        object.__setattr__(self, "title", _text(self.title, "title"))
        object.__setattr__(self, "ordinal", _nonnegative_int(self.ordinal, "ordinal"))
        object.__setattr__(self, "intent", _text(self.intent, "intent"))
        _exact_type(self.state, GoalLanePhaseState, "state")
        _exact_type(self.gate, GoalLanePhaseGate, "gate")
        if type(self.gate_observations) is not tuple:
            raise TypeError("gate_observations must be an exact tuple")
        if type(self.work_associations) is not tuple:
            raise TypeError("work_associations must be an exact tuple")
        observation_refs: set[str] = set()
        exact_satisfaction = False
        current_observation_count = 0
        for observation in self.gate_observations:
            _exact_type(observation, GoalLanePhaseGateObservation, "gate_observation")
            if observation.observation_ref in observation_refs:
                raise GoalPhaseContractError("duplicate gate observation identity")
            observation_refs.add(observation.observation_ref)
            if (
                observation.gate_digest != self.gate.gate_digest
                and observation.outcome is not GoalLanePhaseGateOutcome.STALE
            ):
                raise GoalPhaseContractError(
                    "non-stale observation does not bind the current gate digest"
                )
            if observation.outcome is not GoalLanePhaseGateOutcome.STALE:
                current_observation_count += 1
            exact_satisfaction = exact_satisfaction or (
                observation.gate_digest == self.gate.gate_digest
                and observation.outcome is GoalLanePhaseGateOutcome.SATISFIED
            )
        if current_observation_count > 1:
            raise GoalPhaseContractError(
                "Phase may carry at most one non-stale gate observation"
            )
        work_refs: set[str] = set()
        for association in self.work_associations:
            _exact_type(association, GoalLanePhaseWork, "work_association")
            if association.association_ref in work_refs:
                raise GoalPhaseContractError("duplicate Phase-work identity")
            work_refs.add(association.association_ref)
        if self.state is GoalLanePhaseState.ACCEPTED and not exact_satisfaction:
            raise GoalPhaseContractError(
                "accepted Phase requires a satisfied current-gate observation"
            )
        object.__setattr__(
            self,
            "pursuit_directive",
            _optional_text(self.pursuit_directive, "pursuit_directive"),
        )
        object.__setattr__(
            self,
            "last_receipt_ref",
            None
            if self.last_receipt_ref is None
            else _token(self.last_receipt_ref, "last_receipt_ref"),
        )
        if self.state is GoalLanePhaseState.ACCEPTED and self.last_receipt_ref is None:
            raise GoalPhaseContractError(
                "accepted Phase requires an acceptance publication receipt"
            )
        if (
            self.state is GoalLanePhaseState.ACCEPTED
            and self.last_receipt_ref is not None
            and not _ACCEPTANCE_RECEIPT_REF.fullmatch(self.last_receipt_ref)
        ):
            raise GoalPhaseContractError(
                "accepted Phase receipt must use goal-phase-acceptance domain"
            )


@dataclass(frozen=True, slots=True)
class GoalPhaseDependency:
    owner_goal_tag: str
    dependency_key: str
    dependent: GoalPhaseCoordinate
    prerequisite: GoalPhaseCoordinate
    required_gate_digest: str
    relation: GoalDependencyRelation
    reason: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseDependency:
            raise GoalPhaseContractError("Phase dependency type must be exact")
        object.__setattr__(
            self, "owner_goal_tag", _goal_tag(self.owner_goal_tag, "owner_goal_tag")
        )
        object.__setattr__(
            self,
            "dependency_key",
            _token(self.dependency_key, "dependency_key"),
        )
        _exact_type(self.dependent, GoalPhaseCoordinate, "dependent")
        _exact_type(self.prerequisite, GoalPhaseCoordinate, "prerequisite")
        if self.dependent.goal_tag != self.owner_goal_tag:
            raise GoalPhaseContractError(
                "dependent coordinate must belong to owner Goal"
            )
        if self.dependent == self.prerequisite:
            raise GoalPhaseContractError("Phase dependency cannot depend on itself")
        object.__setattr__(
            self,
            "required_gate_digest",
            _sha256_ref(self.required_gate_digest, "required_gate_digest"),
        )
        _exact_type(self.relation, GoalDependencyRelation, "relation")
        object.__setattr__(self, "reason", _text(self.reason, "reason"))
        object.__setattr__(
            self,
            "evidence_refs",
            _sorted_tokens(self.evidence_refs, "evidence_refs"),
        )


def validate_goal_phase_dependencies(
    dependencies: tuple[GoalPhaseDependency, ...],
) -> None:
    """Reject duplicate Phase-gate declarations and bounded cycles."""

    if type(dependencies) is not tuple:
        raise TypeError("dependencies must be an exact tuple")
    identities: set[tuple[str, str]] = set()
    edges: set[
        tuple[GoalPhaseCoordinate, GoalPhaseCoordinate, GoalDependencyRelation]
    ] = set()
    adjacency: dict[GoalPhaseCoordinate, set[GoalPhaseCoordinate]] = {}
    for dependency in dependencies:
        _exact_type(dependency, GoalPhaseDependency, "dependency")
        identity = (dependency.owner_goal_tag, dependency.dependency_key)
        edge = (dependency.dependent, dependency.prerequisite, dependency.relation)
        if identity in identities or edge in edges:
            raise GoalPhaseContractError("duplicate Phase dependency identity or edge")
        identities.add(identity)
        edges.add(edge)
        adjacency.setdefault(dependency.dependent, set()).add(dependency.prerequisite)
    visiting: set[GoalPhaseCoordinate] = set()
    visited: set[GoalPhaseCoordinate] = set()

    def visit(coordinate: GoalPhaseCoordinate) -> None:
        if coordinate in visiting:
            raise GoalPhaseContractError("Phase dependency cycle in supplied set")
        if coordinate in visited:
            return
        visiting.add(coordinate)
        for prerequisite in adjacency.get(coordinate, ()):
            visit(prerequisite)
        visiting.remove(coordinate)
        visited.add(coordinate)

    for coordinate in adjacency:
        visit(coordinate)


@dataclass(frozen=True, slots=True)
class GoalPhaseContractBundleV1:
    phases: tuple[GoalLanePhase, ...]
    dependencies: tuple[GoalPhaseDependency, ...]
    schema_id: str = GOAL_PHASE_BUNDLE_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseContractBundleV1:
            raise GoalPhaseContractError("bundle type must be exact")
        if self.schema_id != GOAL_PHASE_BUNDLE_SCHEMA:
            raise GoalPhaseContractError("unsupported Goal Phase bundle schema")
        if type(self.phases) is not tuple:
            raise TypeError("phases must be an exact tuple")
        coordinates: dict[GoalPhaseCoordinate, GoalLanePhase] = {}
        for phase in self.phases:
            _exact_type(phase, GoalLanePhase, "phase")
            if phase.coordinate in coordinates:
                raise GoalPhaseContractError("duplicate Phase coordinate")
            coordinates[phase.coordinate] = phase
        validate_goal_phase_dependencies(self.dependencies)
        for dependency in self.dependencies:
            prerequisite = coordinates.get(dependency.prerequisite)
            if (
                prerequisite is not None
                and dependency.required_gate_digest != prerequisite.gate.gate_digest
            ):
                raise GoalPhaseContractError("dependency gate digest is stale")
