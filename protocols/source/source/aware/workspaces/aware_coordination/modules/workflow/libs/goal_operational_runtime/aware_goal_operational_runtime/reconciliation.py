from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from .contracts import IntentContext, JsonObject, TransitionOutcome
from .identity import (
    fingerprint,
    nonnegative,
    optional_text,
    optional_token,
    required_token,
)


class ReconciliationStatus(StrEnum):
    NONE = "none"
    PREPARED = "prepared"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ReconciliationIntentRecord:
    client_intent_id: str
    fingerprint: str

    def __post_init__(self) -> None:
        required_token(self.client_intent_id, "client_intent_id")
        required_token(self.fingerprint, "fingerprint")

    def to_wire(self) -> JsonObject:
        return {
            "client_intent_id": self.client_intent_id,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class GoalReconciliationState:
    status: ReconciliationStatus = ReconciliationStatus.NONE
    revision: int = 0
    canonical_authority_ref: str | None = None
    evidence_ref: str | None = None
    reason: str | None = None
    intent_records: tuple[ReconciliationIntentRecord, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, ReconciliationStatus):
            raise TypeError("status must be ReconciliationStatus")
        nonnegative(self.revision, "revision")
        for field in ("canonical_authority_ref", "evidence_ref"):
            object.__setattr__(self, field, optional_token(getattr(self, field), field))
        object.__setattr__(self, "reason", optional_text(self.reason, "reason"))
        ids = tuple(item.client_intent_id for item in self.intent_records)
        if len(ids) != len(set(ids)):
            raise ValueError("reconciliation intent ids must be unique")
        if self.status is ReconciliationStatus.NONE and any(
            value is not None
            for value in (
                self.canonical_authority_ref,
                self.evidence_ref,
                self.reason,
            )
        ):
            raise ValueError("none reconciliation cannot carry a decision")
        if (
            self.status
            in {
                ReconciliationStatus.PREPARED,
                ReconciliationStatus.ACCEPTED,
            }
            and self.canonical_authority_ref is None
        ):
            raise ValueError("prepared or accepted reconciliation requires authority")
        if self.status is ReconciliationStatus.ACCEPTED and self.evidence_ref is None:
            raise ValueError("accepted reconciliation requires evidence")
        if self.status is ReconciliationStatus.REJECTED and self.reason is None:
            raise ValueError("rejected reconciliation requires reason")

    def to_wire(self) -> JsonObject:
        return {
            "status": self.status.value,
            "revision": self.revision,
            "canonical_authority_ref": self.canonical_authority_ref,
            "evidence_ref": self.evidence_ref,
            "reason": self.reason,
            "intent_records": [item.to_wire() for item in self.intent_records],
        }


@dataclass(frozen=True, slots=True)
class PrepareGoalReconciliationIntent:
    context: IntentContext
    expected_reconciliation_revision: int
    canonical_authority_ref: str
    evidence_ref: str

    def __post_init__(self) -> None:
        nonnegative(
            self.expected_reconciliation_revision,
            "expected_reconciliation_revision",
        )
        required_token(self.canonical_authority_ref, "canonical_authority_ref")
        required_token(self.evidence_ref, "evidence_ref")

    def to_wire(self) -> JsonObject:
        return {
            "kind": "prepare_goal_reconciliation",
            "context": self.context.to_wire(),
            "expected_reconciliation_revision": self.expected_reconciliation_revision,
            "canonical_authority_ref": self.canonical_authority_ref,
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True, slots=True)
class AcceptGoalReconciliationIntent:
    context: IntentContext
    expected_reconciliation_revision: int
    canonical_authority_ref: str
    evidence_ref: str

    def __post_init__(self) -> None:
        nonnegative(
            self.expected_reconciliation_revision,
            "expected_reconciliation_revision",
        )
        required_token(self.canonical_authority_ref, "canonical_authority_ref")
        required_token(self.evidence_ref, "evidence_ref")

    def to_wire(self) -> JsonObject:
        return {
            "kind": "accept_goal_reconciliation",
            "context": self.context.to_wire(),
            "expected_reconciliation_revision": self.expected_reconciliation_revision,
            "canonical_authority_ref": self.canonical_authority_ref,
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True, slots=True)
class RejectGoalReconciliationIntent:
    context: IntentContext
    expected_reconciliation_revision: int
    reason: str

    def __post_init__(self) -> None:
        nonnegative(
            self.expected_reconciliation_revision,
            "expected_reconciliation_revision",
        )
        object.__setattr__(self, "reason", optional_text(self.reason, "reason"))
        if self.reason is None:
            raise ValueError("reason is required")

    def to_wire(self) -> JsonObject:
        return {
            "kind": "reject_goal_reconciliation",
            "context": self.context.to_wire(),
            "expected_reconciliation_revision": self.expected_reconciliation_revision,
            "reason": self.reason,
        }


type GoalReconciliationIntent = (
    PrepareGoalReconciliationIntent
    | AcceptGoalReconciliationIntent
    | RejectGoalReconciliationIntent
)


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    outcome: TransitionOutcome
    state: GoalReconciliationState
    changed: bool = False
    blocker_code: str | None = None


def apply_reconciliation_intent(
    state: GoalReconciliationState,
    intent: GoalReconciliationIntent,
    *,
    authority_generation: int,
) -> ReconciliationResult:
    intent_fingerprint = fingerprint(intent.to_wire())
    existing = next(
        (
            item
            for item in state.intent_records
            if item.client_intent_id == intent.context.client_intent_id
        ),
        None,
    )
    if existing is not None:
        outcome = (
            TransitionOutcome.IDEMPOTENT
            if existing.fingerprint == intent_fingerprint
            else TransitionOutcome.CONFLICT
        )
        blocker = (
            None
            if outcome is TransitionOutcome.IDEMPOTENT
            else "client_intent_id_reused"
        )
        return ReconciliationResult(outcome, state, blocker_code=blocker)
    if not intent.context.actor_evidence.accepted:
        return ReconciliationResult(
            TransitionOutcome.UNAUTHORIZED,
            state,
            blocker_code="actor_not_accepted",
        )
    if intent.context.expected_authority_generation != authority_generation:
        return ReconciliationResult(
            TransitionOutcome.STALE,
            state,
            blocker_code="authority_generation_mismatch",
        )
    if intent.expected_reconciliation_revision != state.revision:
        return ReconciliationResult(
            TransitionOutcome.STALE,
            state,
            blocker_code="reconciliation_revision_mismatch",
        )

    if isinstance(intent, PrepareGoalReconciliationIntent):
        if state.status not in {
            ReconciliationStatus.NONE,
            ReconciliationStatus.REJECTED,
        }:
            return ReconciliationResult(
                TransitionOutcome.INVALID,
                state,
                blocker_code="reconciliation_already_prepared",
            )
        proposed = GoalReconciliationState(
            status=ReconciliationStatus.PREPARED,
            revision=state.revision + 1,
            canonical_authority_ref=intent.canonical_authority_ref,
            evidence_ref=intent.evidence_ref,
            intent_records=state.intent_records,
        )
    elif isinstance(intent, AcceptGoalReconciliationIntent):
        if (
            state.status is not ReconciliationStatus.PREPARED
            or state.canonical_authority_ref != intent.canonical_authority_ref
        ):
            return ReconciliationResult(
                TransitionOutcome.INVALID,
                state,
                blocker_code="reconciliation_not_prepared",
            )
        proposed = replace(
            state,
            status=ReconciliationStatus.ACCEPTED,
            revision=state.revision + 1,
            evidence_ref=intent.evidence_ref,
            reason=None,
        )
    else:
        if state.status is not ReconciliationStatus.PREPARED:
            return ReconciliationResult(
                TransitionOutcome.INVALID,
                state,
                blocker_code="reconciliation_not_prepared",
            )
        proposed = GoalReconciliationState(
            status=ReconciliationStatus.REJECTED,
            revision=state.revision + 1,
            reason=intent.reason,
            intent_records=state.intent_records,
        )

    record = ReconciliationIntentRecord(
        client_intent_id=intent.context.client_intent_id,
        fingerprint=intent_fingerprint,
    )
    proposed = replace(
        proposed,
        intent_records=(*proposed.intent_records, record)[-64:],
    )
    return ReconciliationResult(TransitionOutcome.APPLIED, proposed, changed=True)
