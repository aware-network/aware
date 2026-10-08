from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from .identity import (
    nonnegative,
    normalize_scope_path,
    normalize_tag,
    optional_text,
    optional_token,
    positive,
    required_text,
    required_token,
    unique_by,
)

type JsonObject = dict[str, object]


class IssueStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    CLOSED = "closed"


class IssueTimeAuthority(StrEnum):
    COMMIT_RECEIPT = "commit_receipt"
    SOURCE_DECLARED = "source_declared"
    SOURCE_OBSERVED = "source_observed"
    ACTOR_DECLARED = "actor_declared"
    UNAVAILABLE = "unavailable"


class AuthorityKind(StrEnum):
    LOCAL_OPERATIONAL = "local_operational"
    CANONICAL_COMMITTED = "canonical_committed"
    REPLICATED_CANONICAL = "replicated_canonical"
    DETERMINISTIC_FIXTURE = "deterministic_fixture"


class ReconciliationStatus(StrEnum):
    UNMAPPED = "unmapped"
    MAPPING_PENDING = "mapping_pending"
    MAPPED = "mapped"
    CONFLICT = "conflict"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    NOT_APPLICABLE = "not_applicable"


class TransitionOutcome(StrEnum):
    APPLIED = "applied"
    IDEMPOTENT = "idempotent"
    STALE = "stale"
    CONFLICT = "conflict"
    UNRESOLVED = "unresolved"
    INVALID = "invalid"
    UNAUTHORIZED = "unauthorized"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class ReconciliationState:
    status: ReconciliationStatus
    canonical_authority_ref: str | None = None
    evidence_ref: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, ReconciliationStatus):
            raise TypeError("status must be ReconciliationStatus")
        object.__setattr__(
            self,
            "canonical_authority_ref",
            optional_token(self.canonical_authority_ref, "canonical_authority_ref"),
        )
        object.__setattr__(
            self,
            "evidence_ref",
            optional_token(self.evidence_ref, "evidence_ref"),
        )
        object.__setattr__(self, "reason", optional_text(self.reason, "reason"))
        if (
            self.status
            in {
                ReconciliationStatus.MAPPING_PENDING,
                ReconciliationStatus.MAPPED,
            }
            and self.canonical_authority_ref is None
        ):
            raise ValueError(f"{self.status.value} requires canonical authority ref")
        if self.status is ReconciliationStatus.MAPPED and self.evidence_ref is None:
            raise ValueError("mapped reconciliation requires evidence_ref")
        if self.status is ReconciliationStatus.REJECTED and self.reason is None:
            raise ValueError("rejected reconciliation requires reason")
        if self.status is ReconciliationStatus.NOT_APPLICABLE and any(
            value is not None
            for value in (
                self.canonical_authority_ref,
                self.evidence_ref,
                self.reason,
            )
        ):
            raise ValueError("not_applicable reconciliation carries no evidence")

    def to_wire(self) -> JsonObject:
        return {
            "status": self.status.value,
            "canonical_authority_ref": self.canonical_authority_ref,
            "evidence_ref": self.evidence_ref,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class IssueAuthorityEvidence:
    kind: AuthorityKind
    provider_key: str
    authority_ref: str
    generation: int
    receipt_ref: str | None = None
    reconciliation: ReconciliationState | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AuthorityKind):
            raise TypeError("kind must be AuthorityKind")
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
        if self.reconciliation is not None and not isinstance(
            self.reconciliation, ReconciliationState
        ):
            raise TypeError("reconciliation must be ReconciliationState")
        if self.kind is AuthorityKind.LOCAL_OPERATIONAL:
            if self.reconciliation is None:
                raise ValueError("local authority requires reconciliation state")
            if self.reconciliation.status is ReconciliationStatus.NOT_APPLICABLE:
                raise ValueError("local reconciliation cannot be not_applicable")
        elif self.reconciliation is not None and (
            self.reconciliation.status is not ReconciliationStatus.NOT_APPLICABLE
        ):
            raise ValueError("only local authority carries active reconciliation")

    def to_wire(self) -> JsonObject:
        return {
            "kind": self.kind.value,
            "provider_key": self.provider_key,
            "authority_ref": self.authority_ref,
            "generation": self.generation,
            "receipt_ref": self.receipt_ref,
            "reconciliation": (
                None if self.reconciliation is None else self.reconciliation.to_wire()
            ),
        }


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


@dataclass(frozen=True, slots=True, order=True)
class IssueOwnershipScopePath:
    relative_path: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "relative_path", normalize_scope_path(self.relative_path)
        )

    def to_wire(self) -> JsonObject:
        return {"relative_path": self.relative_path}


@dataclass(frozen=True, slots=True, order=True)
class IssueUpdateLogEntry:
    sequence: int
    message: str
    actor_ref: str
    actor_evidence_ref: str
    outcome: str = "info"
    command: str | None = None
    command_exit_code: int | None = None
    recorded_at: str | None = None
    time_authority: IssueTimeAuthority = IssueTimeAuthority.UNAVAILABLE

    def __post_init__(self) -> None:
        positive(self.sequence, "sequence")
        object.__setattr__(self, "message", required_text(self.message, "message"))
        for name in ("actor_ref", "actor_evidence_ref", "outcome"):
            object.__setattr__(self, name, required_token(getattr(self, name), name))
        object.__setattr__(self, "command", optional_text(self.command, "command"))
        object.__setattr__(
            self, "recorded_at", optional_token(self.recorded_at, "recorded_at")
        )
        if not isinstance(self.time_authority, IssueTimeAuthority):
            raise TypeError("time_authority must be IssueTimeAuthority")
        if self.command_exit_code is not None and self.command is None:
            raise ValueError("command_exit_code requires command")
        if self.recorded_at is None and (
            self.time_authority is not IssueTimeAuthority.UNAVAILABLE
        ):
            raise ValueError("time authority requires recorded_at")
        if self.recorded_at is not None and (
            self.time_authority is IssueTimeAuthority.UNAVAILABLE
        ):
            raise ValueError("recorded_at requires explicit time authority")

    def to_wire(self) -> JsonObject:
        return {
            "sequence": self.sequence,
            "message": self.message,
            "actor_ref": self.actor_ref,
            "actor_evidence_ref": self.actor_evidence_ref,
            "outcome": self.outcome,
            "command": self.command,
            "command_exit_code": self.command_exit_code,
            "recorded_at": self.recorded_at,
            "time_authority": self.time_authority.value,
        }


@dataclass(frozen=True, slots=True, order=True)
class IssueEvidenceRef:
    sequence: int
    path: str
    description: str | None = None

    def __post_init__(self) -> None:
        positive(self.sequence, "sequence")
        object.__setattr__(self, "path", required_token(self.path, "path"))
        object.__setattr__(
            self, "description", optional_text(self.description, "description")
        )

    def to_wire(self) -> JsonObject:
        return {
            "sequence": self.sequence,
            "path": self.path,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class IssueSnapshot:
    issue_ref: str
    tag: str
    title: str
    status: IssueStatus
    priority_level: str
    authority: IssueAuthorityEvidence
    revision: int = 0
    owner_session_id: str | None = None
    overview_content_ref: str | None = None
    scope_paths: tuple[IssueOwnershipScopePath, ...] = ()
    updates: tuple[IssueUpdateLogEntry, ...] = ()
    evidence_refs: tuple[IssueEvidenceRef, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, IssueStatus):
            raise TypeError("status must be IssueStatus")
        if not isinstance(self.authority, IssueAuthorityEvidence):
            raise TypeError("authority must be IssueAuthorityEvidence")
        object.__setattr__(
            self, "issue_ref", required_token(self.issue_ref, "issue_ref")
        )
        object.__setattr__(self, "tag", normalize_tag(self.tag))
        object.__setattr__(self, "title", required_text(self.title, "title"))
        object.__setattr__(
            self,
            "priority_level",
            required_token(self.priority_level, "priority_level").casefold(),
        )
        nonnegative(self.revision, "revision")
        object.__setattr__(
            self,
            "owner_session_id",
            optional_token(self.owner_session_id, "owner_session_id"),
        )
        object.__setattr__(
            self,
            "overview_content_ref",
            optional_token(self.overview_content_ref, "overview_content_ref"),
        )
        unique_by(self.scope_paths, "relative_path", "scope_paths")
        unique_by(self.updates, "sequence", "updates")
        unique_by(self.evidence_refs, "sequence", "evidence_refs")
        if tuple(sorted(self.scope_paths)) != self.scope_paths:
            raise ValueError("scope_paths must be sorted")
        if tuple(item.sequence for item in self.updates) != tuple(
            range(1, len(self.updates) + 1)
        ):
            raise ValueError("updates must have contiguous sequence")
        if tuple(item.sequence for item in self.evidence_refs) != tuple(
            range(1, len(self.evidence_refs) + 1)
        ):
            raise ValueError("evidence_refs must have contiguous sequence")

    def to_wire(self) -> JsonObject:
        return {
            "issue_ref": self.issue_ref,
            "tag": self.tag,
            "title": self.title,
            "status": self.status.value,
            "priority_level": self.priority_level,
            "owner_session_id": self.owner_session_id,
            "overview_content_ref": self.overview_content_ref,
            "scope_paths": [item.to_wire() for item in self.scope_paths],
            "updates": [item.to_wire() for item in self.updates],
            "evidence_refs": [item.to_wire() for item in self.evidence_refs],
            "authority": self.authority.to_wire(),
            "revision": self.revision,
        }


@dataclass(frozen=True, slots=True)
class IntentRecord:
    client_intent_id: str
    fingerprint: str
    outcome: TransitionOutcome
    affected_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("client_intent_id", "fingerprint"):
            object.__setattr__(self, name, required_token(getattr(self, name), name))
        if not isinstance(self.outcome, TransitionOutcome):
            raise TypeError("outcome must be TransitionOutcome")
        if len(self.affected_refs) != len(set(self.affected_refs)):
            raise ValueError("affected_refs must be unique")
        for ref in self.affected_refs:
            required_token(ref, "affected_ref")

    def to_wire(self) -> JsonObject:
        return {
            "client_intent_id": self.client_intent_id,
            "fingerprint": self.fingerprint,
            "outcome": self.outcome.value,
            "affected_refs": list(self.affected_refs),
        }


@dataclass(frozen=True, slots=True)
class IssueOperationalState:
    authority: IssueAuthorityEvidence
    issues: tuple[IssueSnapshot, ...] = ()
    intent_records: tuple[IntentRecord, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.authority, IssueAuthorityEvidence):
            raise TypeError("authority must be IssueAuthorityEvidence")
        unique_by(self.issues, "issue_ref", "issues")
        unique_by(self.issues, "tag", "issues")
        unique_by(self.intent_records, "client_intent_id", "intent_records")
        if tuple(sorted(self.issues, key=lambda item: item.issue_ref)) != self.issues:
            raise ValueError("issues must be sorted")
        if any(item.authority != self.authority for item in self.issues):
            raise ValueError("Issue and runtime authority must match")

    def issue_by_ref(self, issue_ref: str) -> IssueSnapshot | None:
        return next((item for item in self.issues if item.issue_ref == issue_ref), None)

    def issue_by_tag(self, tag: str) -> IssueSnapshot | None:
        normalized = normalize_tag(tag)
        return next((item for item in self.issues if item.tag == normalized), None)

    def to_wire(self) -> JsonObject:
        return {
            "authority": self.authority.to_wire(),
            "issues": [item.to_wire() for item in self.issues],
            "intent_records": [item.to_wire() for item in self.intent_records],
        }


@dataclass(frozen=True, slots=True)
class IssueIntentContext:
    client_intent_id: str
    expected_issue_revision: int | None
    expected_authority_generation: int
    actor_evidence: ActorEvidence

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "client_intent_id",
            required_token(self.client_intent_id, "client_intent_id"),
        )
        if self.expected_issue_revision is not None:
            nonnegative(self.expected_issue_revision, "expected_issue_revision")
        nonnegative(self.expected_authority_generation, "expected_authority_generation")
        if not isinstance(self.actor_evidence, ActorEvidence):
            raise TypeError("actor_evidence must be ActorEvidence")

    def to_wire(self) -> JsonObject:
        return {
            "client_intent_id": self.client_intent_id,
            "expected_issue_revision": self.expected_issue_revision,
            "expected_authority_generation": self.expected_authority_generation,
            "actor_evidence": self.actor_evidence.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class EnsureIssueIntent:
    context: IssueIntentContext
    tag: str
    title: str
    priority_level: str = "medium"
    owner_session_id: str | None = None
    overview_content_ref: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "tag", normalize_tag(self.tag))
        object.__setattr__(self, "title", required_text(self.title, "title"))
        object.__setattr__(
            self,
            "priority_level",
            required_token(self.priority_level, "priority_level").casefold(),
        )
        object.__setattr__(
            self,
            "owner_session_id",
            optional_token(self.owner_session_id, "owner_session_id"),
        )
        object.__setattr__(
            self,
            "overview_content_ref",
            optional_token(self.overview_content_ref, "overview_content_ref"),
        )

    def to_wire(self) -> JsonObject:
        return _intent_wire(
            "ensure_issue",
            self.context,
            tag=self.tag,
            title=self.title,
            priority_level=self.priority_level,
            owner_session_id=self.owner_session_id,
            overview_content_ref=self.overview_content_ref,
        )


@dataclass(frozen=True, slots=True)
class IssueTargetIntent:
    context: IssueIntentContext
    issue_ref: str
    kind: ClassVar[str] = "issue_target"

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "issue_ref", required_token(self.issue_ref, "issue_ref")
        )

    def to_wire(self) -> JsonObject:
        return _intent_wire(self.kind, self.context, issue_ref=self.issue_ref)


@dataclass(frozen=True, slots=True)
class StartIssueProgressIntent(IssueTargetIntent):
    kind: ClassVar[str] = "start_issue_progress"


@dataclass(frozen=True, slots=True)
class BlockIssueIntent(IssueTargetIntent):
    kind: ClassVar[str] = "block_issue"


@dataclass(frozen=True, slots=True)
class ResumeIssueIntent(IssueTargetIntent):
    kind: ClassVar[str] = "resume_issue"


@dataclass(frozen=True, slots=True)
class SetIssueOwnerIntent(IssueTargetIntent):
    new_owner_session_id: str = ""
    kind: ClassVar[str] = "set_issue_owner"

    def __post_init__(self) -> None:
        IssueTargetIntent.__post_init__(self)
        object.__setattr__(
            self,
            "new_owner_session_id",
            required_token(self.new_owner_session_id, "new_owner_session_id"),
        )

    def to_wire(self) -> JsonObject:
        return _intent_wire(
            self.kind,
            self.context,
            issue_ref=self.issue_ref,
            new_owner_session_id=self.new_owner_session_id,
        )


@dataclass(frozen=True, slots=True)
class ReopenIssueIntent(IssueTargetIntent):
    kind: ClassVar[str] = "reopen_issue"


@dataclass(frozen=True, slots=True)
class CloseIssueIntent(IssueTargetIntent):
    kind: ClassVar[str] = "close_issue"


@dataclass(frozen=True, slots=True)
class BindIssueScopePathsIntent(IssueTargetIntent):
    scope_paths: tuple[IssueOwnershipScopePath, ...] = ()
    kind: ClassVar[str] = "bind_issue_scope_paths"

    def __post_init__(self) -> None:
        IssueTargetIntent.__post_init__(self)
        unique_by(self.scope_paths, "relative_path", "scope_paths")
        normalized = tuple(sorted(self.scope_paths))
        object.__setattr__(self, "scope_paths", normalized)

    def to_wire(self) -> JsonObject:
        return _intent_wire(
            self.kind,
            self.context,
            issue_ref=self.issue_ref,
            scope_paths=[item.to_wire() for item in self.scope_paths],
        )


@dataclass(frozen=True, slots=True)
class AmendIssueScopePathsIntent(IssueTargetIntent):
    owner_session_id: str = ""
    add_scope_paths: tuple[IssueOwnershipScopePath, ...] = ()
    kind: ClassVar[str] = "amend_issue_scope_paths"

    def __post_init__(self) -> None:
        IssueTargetIntent.__post_init__(self)
        if self.context.expected_issue_revision is None:
            raise ValueError("expected_issue_revision is required for scope amendment")
        object.__setattr__(
            self,
            "owner_session_id",
            required_token(self.owner_session_id, "owner_session_id"),
        )
        if not self.add_scope_paths:
            raise ValueError("add_scope_paths must not be empty")
        unique_by(self.add_scope_paths, "relative_path", "add_scope_paths")
        object.__setattr__(self, "add_scope_paths", tuple(sorted(self.add_scope_paths)))

    def to_wire(self) -> JsonObject:
        return _intent_wire(
            self.kind,
            self.context,
            issue_ref=self.issue_ref,
            owner_session_id=self.owner_session_id,
            add_scope_paths=[item.to_wire() for item in self.add_scope_paths],
        )


@dataclass(frozen=True, slots=True)
class AppendIssueUpdateIntent(IssueTargetIntent):
    message: str = ""
    outcome: str = "info"
    command: str | None = None
    command_exit_code: int | None = None
    recorded_at: str | None = None
    time_authority: IssueTimeAuthority = IssueTimeAuthority.UNAVAILABLE
    attributed_actor_ref: str | None = None
    attributed_actor_evidence_ref: str | None = None
    kind: ClassVar[str] = "append_issue_update"

    def __post_init__(self) -> None:
        IssueTargetIntent.__post_init__(self)
        object.__setattr__(self, "message", required_text(self.message, "message"))
        object.__setattr__(self, "outcome", required_token(self.outcome, "outcome"))
        object.__setattr__(self, "command", optional_text(self.command, "command"))
        object.__setattr__(
            self, "recorded_at", optional_token(self.recorded_at, "recorded_at")
        )
        object.__setattr__(
            self,
            "attributed_actor_ref",
            optional_token(self.attributed_actor_ref, "attributed_actor_ref"),
        )
        object.__setattr__(
            self,
            "attributed_actor_evidence_ref",
            optional_token(
                self.attributed_actor_evidence_ref,
                "attributed_actor_evidence_ref",
            ),
        )
        if (self.attributed_actor_ref is None) != (
            self.attributed_actor_evidence_ref is None
        ):
            raise ValueError("attributed actor fields must be present together")
        if not isinstance(self.time_authority, IssueTimeAuthority):
            raise TypeError("time_authority must be IssueTimeAuthority")
        if self.command_exit_code is not None and self.command is None:
            raise ValueError("command_exit_code requires command")
        if self.recorded_at is None and (
            self.time_authority is not IssueTimeAuthority.UNAVAILABLE
        ):
            raise ValueError("time authority requires recorded_at")
        if self.recorded_at is not None and (
            self.time_authority is IssueTimeAuthority.UNAVAILABLE
        ):
            raise ValueError("recorded_at requires explicit time authority")

    def to_wire(self) -> JsonObject:
        return _intent_wire(
            self.kind,
            self.context,
            issue_ref=self.issue_ref,
            message=self.message,
            outcome=self.outcome,
            command=self.command,
            command_exit_code=self.command_exit_code,
            recorded_at=self.recorded_at,
            time_authority=self.time_authority.value,
            attributed_actor_ref=self.attributed_actor_ref,
            attributed_actor_evidence_ref=self.attributed_actor_evidence_ref,
        )


@dataclass(frozen=True, slots=True)
class AppendIssueEvidenceIntent(IssueTargetIntent):
    path: str = ""
    description: str | None = None
    kind: ClassVar[str] = "append_issue_evidence"

    def __post_init__(self) -> None:
        IssueTargetIntent.__post_init__(self)
        object.__setattr__(self, "path", required_token(self.path, "path"))
        object.__setattr__(
            self, "description", optional_text(self.description, "description")
        )

    def to_wire(self) -> JsonObject:
        return _intent_wire(
            self.kind,
            self.context,
            issue_ref=self.issue_ref,
            path=self.path,
            description=self.description,
        )


@dataclass(frozen=True, slots=True)
class PrepareAuthorityReconciliationIntent:
    context: IssueIntentContext
    canonical_authority_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_authority_ref",
            required_token(self.canonical_authority_ref, "canonical_authority_ref"),
        )

    def to_wire(self) -> JsonObject:
        return _intent_wire(
            "prepare_authority_reconciliation",
            self.context,
            canonical_authority_ref=self.canonical_authority_ref,
        )


@dataclass(frozen=True, slots=True)
class AcceptAuthorityMappingIntent:
    context: IssueIntentContext
    canonical_authority_ref: str
    evidence_ref: str

    def __post_init__(self) -> None:
        for name in ("canonical_authority_ref", "evidence_ref"):
            object.__setattr__(self, name, required_token(getattr(self, name), name))

    def to_wire(self) -> JsonObject:
        return _intent_wire(
            "accept_authority_mapping",
            self.context,
            canonical_authority_ref=self.canonical_authority_ref,
            evidence_ref=self.evidence_ref,
        )


@dataclass(frozen=True, slots=True)
class RejectAuthorityMappingIntent:
    context: IssueIntentContext
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason", required_text(self.reason, "reason"))

    def to_wire(self) -> JsonObject:
        return _intent_wire(
            "reject_authority_mapping", self.context, reason=self.reason
        )


type IssueIntent = (
    EnsureIssueIntent
    | StartIssueProgressIntent
    | BlockIssueIntent
    | ResumeIssueIntent
    | SetIssueOwnerIntent
    | ReopenIssueIntent
    | CloseIssueIntent
    | BindIssueScopePathsIntent
    | AmendIssueScopePathsIntent
    | AppendIssueUpdateIntent
    | AppendIssueEvidenceIntent
    | PrepareAuthorityReconciliationIntent
    | AcceptAuthorityMappingIntent
    | RejectAuthorityMappingIntent
)


@dataclass(frozen=True, slots=True)
class TransitionResult:
    outcome: TransitionOutcome
    state: IssueOperationalState
    changed: bool = False
    issue_ref: str | None = None
    issue_revision: int | None = None
    affected_refs: tuple[str, ...] = ()
    blocker_code: str | None = None


def _intent_wire(
    kind: str,
    context: IssueIntentContext,
    **payload: object,
) -> JsonObject:
    return {"kind": kind, "context": context.to_wire(), **payload}
