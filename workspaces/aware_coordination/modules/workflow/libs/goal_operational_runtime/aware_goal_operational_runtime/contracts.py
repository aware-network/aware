from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .identity import (
    nonnegative,
    normalize_goal_tag,
    optional_text,
    optional_token,
    positive,
    required_text,
    required_token,
    unique_tokens,
)

type JsonObject = dict[str, object]


class GoalStatus(StrEnum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    BLOCKED = "blocked"
    PARKED = "parked"
    ACHIEVED = "achieved"
    SUPERSEDED = "superseded"


class GoalLaneStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    READY = "ready"
    BLOCKED = "blocked"
    CLOSED = "closed"


class GoalLaneIssueTick(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETE = "complete"
    BLOCKED = "blocked"


class GoalAuthorityKind(StrEnum):
    LOCAL_OPERATIONAL = "local_operational"
    CANONICAL_COMMITTED = "canonical_committed"
    REPLICATED_CANONICAL = "replicated_canonical"
    DETERMINISTIC_FIXTURE = "deterministic_fixture"


class TransitionOutcome(StrEnum):
    APPLIED = "applied"
    IDEMPOTENT = "idempotent"
    STALE = "stale"
    CONFLICT = "conflict"
    UNRESOLVED = "unresolved"
    INVALID = "invalid"
    UNAUTHORIZED = "unauthorized"


@dataclass(frozen=True, slots=True)
class ActorEvidence:
    actor_ref: str
    evidence_ref: str
    accepted: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "actor_ref", required_token(self.actor_ref, "actor_ref")
        )
        object.__setattr__(
            self, "evidence_ref", required_token(self.evidence_ref, "evidence_ref")
        )
        if not isinstance(self.accepted, bool):
            raise TypeError("accepted must be bool")

    def to_wire(self) -> JsonObject:
        return {
            "actor_ref": self.actor_ref,
            "evidence_ref": self.evidence_ref,
            "accepted": self.accepted,
        }


@dataclass(frozen=True, slots=True)
class GoalAuthorityEvidence:
    kind: GoalAuthorityKind
    provider_key: str
    authority_ref: str
    generation: int
    receipt_ref: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, GoalAuthorityKind):
            raise TypeError("kind must be GoalAuthorityKind")
        object.__setattr__(
            self, "provider_key", required_token(self.provider_key, "provider_key")
        )
        object.__setattr__(
            self, "authority_ref", required_token(self.authority_ref, "authority_ref")
        )
        nonnegative(self.generation, "generation")
        object.__setattr__(
            self, "receipt_ref", optional_token(self.receipt_ref, "receipt_ref")
        )

    def to_wire(self) -> JsonObject:
        return {
            "kind": self.kind.value,
            "provider_key": self.provider_key,
            "authority_ref": self.authority_ref,
            "generation": self.generation,
            "receipt_ref": self.receipt_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalIntegratedUpdate:
    update_key: str
    sequence: int
    kind: str
    message: str
    actor_ref: str
    actor_evidence_ref: str
    recorded_at: str | None = None
    lane_ref: str | None = None
    row_ref: str | None = None
    receipt_ref: str | None = None

    def __post_init__(self) -> None:
        for field in ("update_key", "kind", "actor_ref", "actor_evidence_ref"):
            object.__setattr__(self, field, required_token(getattr(self, field), field))
        positive(self.sequence, "sequence")
        object.__setattr__(self, "message", required_text(self.message, "message"))
        for field in ("recorded_at", "lane_ref", "row_ref", "receipt_ref"):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))
        if self.row_ref is not None and self.lane_ref is None:
            raise ValueError("row_ref requires lane_ref")

    def to_wire(self) -> JsonObject:
        return {
            "update_key": self.update_key,
            "sequence": self.sequence,
            "kind": self.kind,
            "message": self.message,
            "actor_ref": self.actor_ref,
            "actor_evidence_ref": self.actor_evidence_ref,
            "recorded_at": self.recorded_at,
            "lane_ref": self.lane_ref,
            "row_ref": self.row_ref,
            "receipt_ref": self.receipt_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalLaneIssueSnapshot:
    row_ref: str
    row_key: str
    sequence: int
    gate: str
    tick: GoalLaneIssueTick = GoalLaneIssueTick.PLANNED
    status_snapshot: str = "Planned"
    previous_row_ref: str | None = None
    prerequisite_refs: tuple[str, ...] = ()
    planned_issue_tag: str | None = None
    issue_ref: str | None = None
    issue_authority_receipt_ref: str | None = None
    issue_observation_ref: str | None = None
    owner_execution_id: str | None = None
    receipt_ref: str | None = None
    revision: int = 0

    def __post_init__(self) -> None:
        for field in ("row_ref", "row_key"):
            object.__setattr__(self, field, required_token(getattr(self, field), field))
        positive(self.sequence, "sequence")
        object.__setattr__(self, "gate", required_text(self.gate, "gate"))
        if not isinstance(self.tick, GoalLaneIssueTick):
            raise TypeError("tick must be GoalLaneIssueTick")
        object.__setattr__(
            self,
            "status_snapshot",
            required_text(self.status_snapshot, "status_snapshot"),
        )
        for field in (
            "previous_row_ref",
            "planned_issue_tag",
            "issue_ref",
            "issue_authority_receipt_ref",
            "issue_observation_ref",
            "owner_execution_id",
            "receipt_ref",
        ):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))
        object.__setattr__(
            self,
            "prerequisite_refs",
            unique_tokens(self.prerequisite_refs, "prerequisite_ref"),
        )
        nonnegative(self.revision, "revision")
        if self.issue_ref is None and any(
            value is not None
            for value in (self.issue_authority_receipt_ref, self.issue_observation_ref)
        ):
            raise ValueError("Issue receipts require issue_ref")
        if self.issue_ref is not None and self.issue_authority_receipt_ref is None:
            raise ValueError("issue_ref requires issue_authority_receipt_ref")

    def to_wire(self) -> JsonObject:
        return {
            "row_ref": self.row_ref,
            "row_key": self.row_key,
            "sequence": self.sequence,
            "gate": self.gate,
            "tick": self.tick.value,
            "status_snapshot": self.status_snapshot,
            "previous_row_ref": self.previous_row_ref,
            "prerequisite_refs": list(self.prerequisite_refs),
            "planned_issue_tag": self.planned_issue_tag,
            "issue_ref": self.issue_ref,
            "issue_authority_receipt_ref": self.issue_authority_receipt_ref,
            "issue_observation_ref": self.issue_observation_ref,
            "owner_execution_id": self.owner_execution_id,
            "receipt_ref": self.receipt_ref,
            "revision": self.revision,
        }


@dataclass(frozen=True, slots=True)
class GoalLaneSnapshot:
    lane_ref: str
    lane_key: str
    status: GoalLaneStatus = GoalLaneStatus.PLANNED
    role_key: str | None = None
    role_label: str | None = None
    owner_execution_id: str | None = None
    scope: str | None = None
    head_row_ref: str | None = None
    rows: tuple[GoalLaneIssueSnapshot, ...] = ()
    revision: int = 0

    def __post_init__(self) -> None:
        for field in ("lane_ref", "lane_key"):
            object.__setattr__(self, field, required_token(getattr(self, field), field))
        if not isinstance(self.status, GoalLaneStatus):
            raise TypeError("status must be GoalLaneStatus")
        for field in ("role_key", "owner_execution_id", "head_row_ref"):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))
        for field in ("role_label", "scope"):
            object.__setattr__(self, field, optional_text(getattr(self, field), field))
        nonnegative(self.revision, "revision")
        if len({row.row_ref for row in self.rows}) != len(self.rows):
            raise ValueError("row_ref must be unique within lane")
        if len({row.row_key for row in self.rows}) != len(self.rows):
            raise ValueError("row_key must be unique within lane")
        if tuple(row.sequence for row in self.rows) != tuple(
            range(1, len(self.rows) + 1)
        ):
            raise ValueError("lane row sequence must be contiguous from one")
        expected_head = None if not self.rows else self.rows[-1].row_ref
        if self.head_row_ref != expected_head:
            raise ValueError("head_row_ref must identify the final lane row")

    def row_by_ref(self, row_ref: str) -> GoalLaneIssueSnapshot | None:
        return next((row for row in self.rows if row.row_ref == row_ref), None)

    def row_by_key(self, row_key: str) -> GoalLaneIssueSnapshot | None:
        return next((row for row in self.rows if row.row_key == row_key), None)

    def to_wire(self) -> JsonObject:
        return {
            "lane_ref": self.lane_ref,
            "lane_key": self.lane_key,
            "status": self.status.value,
            "role_key": self.role_key,
            "role_label": self.role_label,
            "owner_execution_id": self.owner_execution_id,
            "scope": self.scope,
            "head_row_ref": self.head_row_ref,
            "rows": [row.to_wire() for row in self.rows],
            "revision": self.revision,
        }


@dataclass(frozen=True, slots=True)
class GoalSnapshot:
    goal_ref: str
    tag: str
    title: str
    status: GoalStatus = GoalStatus.PROPOSED
    priority_level: str = "medium"
    definition_of_done_ref: str | None = None
    locks_ref: str | None = None
    evidence_ref: str | None = None
    lanes: tuple[GoalLaneSnapshot, ...] = ()
    updates: tuple[GoalIntegratedUpdate, ...] = ()
    revision: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "goal_ref", required_token(self.goal_ref, "goal_ref"))
        object.__setattr__(self, "tag", normalize_goal_tag(self.tag))
        object.__setattr__(self, "title", required_text(self.title, "title"))
        if not isinstance(self.status, GoalStatus):
            raise TypeError("status must be GoalStatus")
        object.__setattr__(
            self,
            "priority_level",
            required_token(self.priority_level, "priority_level"),
        )
        for field in ("definition_of_done_ref", "locks_ref", "evidence_ref"):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))
        nonnegative(self.revision, "revision")
        if len({lane.lane_ref for lane in self.lanes}) != len(self.lanes):
            raise ValueError("lane_ref must be unique within goal")
        if len({lane.lane_key for lane in self.lanes}) != len(self.lanes):
            raise ValueError("lane_key must be unique within goal")
        if tuple(update.sequence for update in self.updates) != tuple(
            range(1, len(self.updates) + 1)
        ):
            raise ValueError("Goal update sequence must be contiguous from one")
        if len({update.update_key for update in self.updates}) != len(self.updates):
            raise ValueError("Goal update keys must be unique")

    @property
    def update_head_key(self) -> str | None:
        return None if not self.updates else self.updates[-1].update_key

    def lane_by_ref(self, lane_ref: str) -> GoalLaneSnapshot | None:
        return next((lane for lane in self.lanes if lane.lane_ref == lane_ref), None)

    def lane_by_key(self, lane_key: str) -> GoalLaneSnapshot | None:
        return next((lane for lane in self.lanes if lane.lane_key == lane_key), None)

    def to_wire(self) -> JsonObject:
        return {
            "goal_ref": self.goal_ref,
            "tag": self.tag,
            "title": self.title,
            "status": self.status.value,
            "priority_level": self.priority_level,
            "definition_of_done_ref": self.definition_of_done_ref,
            "locks_ref": self.locks_ref,
            "evidence_ref": self.evidence_ref,
            "lanes": [lane.to_wire() for lane in self.lanes],
            "updates": [update.to_wire() for update in self.updates],
            "revision": self.revision,
        }


@dataclass(frozen=True, slots=True)
class IntentContext:
    client_intent_id: str
    expected_authority_generation: int
    actor_evidence: ActorEvidence

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "client_intent_id",
            required_token(self.client_intent_id, "client_intent_id"),
        )
        nonnegative(self.expected_authority_generation, "expected_authority_generation")
        if not isinstance(self.actor_evidence, ActorEvidence):
            raise TypeError("actor_evidence must be ActorEvidence")

    def to_wire(self) -> JsonObject:
        return {
            "client_intent_id": self.client_intent_id,
            "expected_authority_generation": self.expected_authority_generation,
            "actor_evidence": self.actor_evidence.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class EnsureGoalIntent:
    context: IntentContext
    tag: str
    title: str
    priority_level: str = "medium"
    definition_of_done_ref: str | None = None
    locks_ref: str | None = None
    evidence_ref: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "tag", normalize_goal_tag(self.tag))
        object.__setattr__(self, "title", required_text(self.title, "title"))
        object.__setattr__(
            self,
            "priority_level",
            required_token(self.priority_level, "priority_level"),
        )
        for field in ("definition_of_done_ref", "locks_ref", "evidence_ref"):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))

    def to_wire(self) -> JsonObject:
        return {
            "kind": "ensure_goal",
            "context": self.context.to_wire(),
            "tag": self.tag,
            "title": self.title,
            "priority_level": self.priority_level,
            "definition_of_done_ref": self.definition_of_done_ref,
            "locks_ref": self.locks_ref,
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalLifecycleIntent:
    context: IntentContext
    goal_ref: str
    expected_goal_revision: int
    evidence_ref: str | None = None
    reason: str | None = None

    operation: str = "lifecycle"

    def __post_init__(self) -> None:
        object.__setattr__(self, "goal_ref", required_token(self.goal_ref, "goal_ref"))
        nonnegative(self.expected_goal_revision, "expected_goal_revision")
        object.__setattr__(
            self, "evidence_ref", optional_token(self.evidence_ref, "evidence_ref")
        )
        object.__setattr__(self, "reason", optional_text(self.reason, "reason"))

    def to_wire(self) -> JsonObject:
        return {
            "kind": self.operation,
            "context": self.context.to_wire(),
            "goal_ref": self.goal_ref,
            "expected_goal_revision": self.expected_goal_revision,
            "evidence_ref": self.evidence_ref,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class ActivateGoalIntent(GoalLifecycleIntent):
    operation: str = "activate_goal"


@dataclass(frozen=True, slots=True)
class BlockGoalIntent(GoalLifecycleIntent):
    operation: str = "block_goal"


@dataclass(frozen=True, slots=True)
class ResumeGoalIntent(GoalLifecycleIntent):
    operation: str = "resume_goal"


@dataclass(frozen=True, slots=True)
class ParkGoalIntent(GoalLifecycleIntent):
    operation: str = "park_goal"


@dataclass(frozen=True, slots=True)
class AchieveGoalIntent(GoalLifecycleIntent):
    operation: str = "achieve_goal"


@dataclass(frozen=True, slots=True)
class SupersedeGoalIntent(GoalLifecycleIntent):
    operation: str = "supersede_goal"


@dataclass(frozen=True, slots=True)
class EnsureGoalLaneIntent:
    context: IntentContext
    goal_ref: str
    expected_goal_revision: int
    lane_key: str
    status: GoalLaneStatus = GoalLaneStatus.PLANNED
    role_key: str | None = None
    role_label: str | None = None
    owner_execution_id: str | None = None
    scope: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "goal_ref", required_token(self.goal_ref, "goal_ref"))
        nonnegative(self.expected_goal_revision, "expected_goal_revision")
        object.__setattr__(self, "lane_key", required_token(self.lane_key, "lane_key"))
        if not isinstance(self.status, GoalLaneStatus):
            raise TypeError("status must be GoalLaneStatus")
        for field in ("role_key", "owner_execution_id"):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))
        for field in ("role_label", "scope"):
            object.__setattr__(self, field, optional_text(getattr(self, field), field))

    def to_wire(self) -> JsonObject:
        return {
            "kind": "ensure_goal_lane",
            "context": self.context.to_wire(),
            "goal_ref": self.goal_ref,
            "expected_goal_revision": self.expected_goal_revision,
            "lane_key": self.lane_key,
            "status": self.status.value,
            "role_key": self.role_key,
            "role_label": self.role_label,
            "owner_execution_id": self.owner_execution_id,
            "scope": self.scope,
        }


@dataclass(frozen=True, slots=True)
class AppendGoalLaneIssueIntent:
    context: IntentContext
    goal_ref: str
    lane_ref: str
    expected_lane_revision: int
    expected_head_row_ref: str | None
    row_key: str
    gate: str
    prerequisite_refs: tuple[str, ...] = ()
    planned_issue_tag: str | None = None
    owner_execution_id: str | None = None

    def __post_init__(self) -> None:
        for field in ("goal_ref", "lane_ref", "row_key"):
            object.__setattr__(self, field, required_token(getattr(self, field), field))
        nonnegative(self.expected_lane_revision, "expected_lane_revision")
        object.__setattr__(
            self,
            "expected_head_row_ref",
            optional_token(self.expected_head_row_ref, "expected_head_row_ref"),
        )
        object.__setattr__(self, "gate", required_text(self.gate, "gate"))
        object.__setattr__(
            self,
            "prerequisite_refs",
            unique_tokens(self.prerequisite_refs, "prerequisite_ref"),
        )
        for field in ("planned_issue_tag", "owner_execution_id"):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))

    def to_wire(self) -> JsonObject:
        return {
            "kind": "append_goal_lane_issue",
            "context": self.context.to_wire(),
            "goal_ref": self.goal_ref,
            "lane_ref": self.lane_ref,
            "expected_lane_revision": self.expected_lane_revision,
            "expected_head_row_ref": self.expected_head_row_ref,
            "row_key": self.row_key,
            "gate": self.gate,
            "prerequisite_refs": list(self.prerequisite_refs),
            "planned_issue_tag": self.planned_issue_tag,
            "owner_execution_id": self.owner_execution_id,
        }


@dataclass(frozen=True, slots=True)
class LinkGoalLaneIssueIntent:
    context: IntentContext
    goal_ref: str
    lane_ref: str
    row_ref: str
    expected_lane_revision: int
    expected_row_revision: int
    issue_ref: str
    issue_authority_receipt_ref: str

    def __post_init__(self) -> None:
        for field in (
            "goal_ref",
            "lane_ref",
            "row_ref",
            "issue_ref",
            "issue_authority_receipt_ref",
        ):
            object.__setattr__(self, field, required_token(getattr(self, field), field))
        nonnegative(self.expected_lane_revision, "expected_lane_revision")
        nonnegative(self.expected_row_revision, "expected_row_revision")

    def to_wire(self) -> JsonObject:
        return {
            "kind": "link_goal_lane_issue",
            "context": self.context.to_wire(),
            "goal_ref": self.goal_ref,
            "lane_ref": self.lane_ref,
            "row_ref": self.row_ref,
            "expected_lane_revision": self.expected_lane_revision,
            "expected_row_revision": self.expected_row_revision,
            "issue_ref": self.issue_ref,
            "issue_authority_receipt_ref": self.issue_authority_receipt_ref,
        }


@dataclass(frozen=True, slots=True)
class SyncGoalLaneIssueIntent:
    context: IntentContext
    goal_ref: str
    lane_ref: str
    row_ref: str
    expected_lane_revision: int
    expected_row_revision: int
    issue_ref: str
    issue_observation_ref: str
    status_snapshot: str
    tick: GoalLaneIssueTick
    owner_execution_id: str | None = None
    receipt_ref: str | None = None

    def __post_init__(self) -> None:
        for field in (
            "goal_ref",
            "lane_ref",
            "row_ref",
            "issue_ref",
            "issue_observation_ref",
        ):
            object.__setattr__(self, field, required_token(getattr(self, field), field))
        nonnegative(self.expected_lane_revision, "expected_lane_revision")
        nonnegative(self.expected_row_revision, "expected_row_revision")
        object.__setattr__(
            self,
            "status_snapshot",
            required_text(self.status_snapshot, "status_snapshot"),
        )
        if not isinstance(self.tick, GoalLaneIssueTick):
            raise TypeError("tick must be GoalLaneIssueTick")
        for field in ("owner_execution_id", "receipt_ref"):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))

    def to_wire(self) -> JsonObject:
        return {
            "kind": "sync_goal_lane_issue",
            "context": self.context.to_wire(),
            "goal_ref": self.goal_ref,
            "lane_ref": self.lane_ref,
            "row_ref": self.row_ref,
            "expected_lane_revision": self.expected_lane_revision,
            "expected_row_revision": self.expected_row_revision,
            "issue_ref": self.issue_ref,
            "issue_observation_ref": self.issue_observation_ref,
            "status_snapshot": self.status_snapshot,
            "tick": self.tick.value,
            "owner_execution_id": self.owner_execution_id,
            "receipt_ref": self.receipt_ref,
        }


@dataclass(frozen=True, slots=True)
class AppendGoalUpdateIntent:
    context: IntentContext
    goal_ref: str
    expected_update_head_key: str | None
    update_key: str
    kind: str
    message: str
    recorded_at: str | None = None
    lane_ref: str | None = None
    row_ref: str | None = None
    receipt_ref: str | None = None

    def __post_init__(self) -> None:
        for field in ("goal_ref", "update_key", "kind"):
            object.__setattr__(self, field, required_token(getattr(self, field), field))
        object.__setattr__(
            self,
            "expected_update_head_key",
            optional_token(self.expected_update_head_key, "expected_update_head_key"),
        )
        object.__setattr__(self, "message", required_text(self.message, "message"))
        for field in ("recorded_at", "lane_ref", "row_ref", "receipt_ref"):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))
        if self.row_ref is not None and self.lane_ref is None:
            raise ValueError("row_ref requires lane_ref")

    def to_wire(self) -> JsonObject:
        return {
            "kind": "append_goal_update",
            "context": self.context.to_wire(),
            "goal_ref": self.goal_ref,
            "expected_update_head_key": self.expected_update_head_key,
            "update_key": self.update_key,
            "kind_token": self.kind,
            "message": self.message,
            "recorded_at": self.recorded_at,
            "lane_ref": self.lane_ref,
            "row_ref": self.row_ref,
            "receipt_ref": self.receipt_ref,
        }


type GoalIntent = (
    EnsureGoalIntent
    | GoalLifecycleIntent
    | EnsureGoalLaneIntent
    | AppendGoalLaneIssueIntent
    | LinkGoalLaneIssueIntent
    | SyncGoalLaneIssueIntent
    | AppendGoalUpdateIntent
)


@dataclass(frozen=True, slots=True)
class IntentRecord:
    client_intent_id: str
    fingerprint: str
    outcome: TransitionOutcome
    goal_ref: str | None = None
    lane_ref: str | None = None
    row_ref: str | None = None

    def __post_init__(self) -> None:
        for field in ("client_intent_id", "fingerprint"):
            object.__setattr__(self, field, required_token(getattr(self, field), field))
        if not isinstance(self.outcome, TransitionOutcome):
            raise TypeError("outcome must be TransitionOutcome")
        for field in ("goal_ref", "lane_ref", "row_ref"):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))

    def to_wire(self) -> JsonObject:
        return {
            "client_intent_id": self.client_intent_id,
            "fingerprint": self.fingerprint,
            "outcome": self.outcome.value,
            "goal_ref": self.goal_ref,
            "lane_ref": self.lane_ref,
            "row_ref": self.row_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalOperationalState:
    authority: GoalAuthorityEvidence
    goals: tuple[GoalSnapshot, ...] = ()
    intent_records: tuple[IntentRecord, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.authority, GoalAuthorityEvidence):
            raise TypeError("authority must be GoalAuthorityEvidence")
        if len({goal.goal_ref for goal in self.goals}) != len(self.goals):
            raise ValueError("goal_ref must be unique")
        if len({goal.tag for goal in self.goals}) != len(self.goals):
            raise ValueError("Goal tag must be unique")
        if len({item.client_intent_id for item in self.intent_records}) != len(
            self.intent_records
        ):
            raise ValueError("client intent ids must be unique")

    def goal_by_ref(self, goal_ref: str) -> GoalSnapshot | None:
        return next((goal for goal in self.goals if goal.goal_ref == goal_ref), None)

    def goal_by_tag(self, tag: str) -> GoalSnapshot | None:
        normalized = normalize_goal_tag(tag)
        return next((goal for goal in self.goals if goal.tag == normalized), None)

    def to_wire(self) -> JsonObject:
        return {
            "authority": self.authority.to_wire(),
            "goals": [goal.to_wire() for goal in self.goals],
            "intent_records": [item.to_wire() for item in self.intent_records],
        }


@dataclass(frozen=True, slots=True)
class TransitionResult:
    outcome: TransitionOutcome
    state: GoalOperationalState
    changed: bool = False
    blocker_code: str | None = None
    goal_ref: str | None = None
    lane_ref: str | None = None
    row_ref: str | None = None
    goal_revision: int | None = None
    lane_revision: int | None = None
    row_revision: int | None = None
    actual_head_row_ref: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, TransitionOutcome):
            raise TypeError("outcome must be TransitionOutcome")
        for field in (
            "blocker_code",
            "goal_ref",
            "lane_ref",
            "row_ref",
            "actual_head_row_ref",
        ):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))
        for field in ("goal_revision", "lane_revision", "row_revision"):
            value = getattr(self, field)
            if value is not None:
                nonnegative(value, field)
        if self.changed and self.outcome is not TransitionOutcome.APPLIED:
            raise ValueError("only applied transitions may report changed")
