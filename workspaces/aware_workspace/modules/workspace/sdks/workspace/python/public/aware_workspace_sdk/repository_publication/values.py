"""SDK-owned publication values; detached evidence cannot grant authority.

The canonical declarations are repository_publication_values.aware. These
authored Python bindings preserve the existing writer's field types, including
its list fields. Codec entry points validate and detach them; construction does
not select a provider, authorize work or evaluate Issue/Workspace policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WorkspacePublicationState = Literal["not_published", "published", "unknown"]
WorkspaceReferenceUpdateState = Literal[
    "not_run", "cas_applied", "cas_failed", "unknown"
]
WorkspaceIndexProjectionState = Literal[
    "not_run", "applied", "pending", "failed", "unknown"
]
WorkspaceCleanupState = Literal["not_attempted", "completed", "incomplete", "unknown"]
WorkspacePhysicalEffectKind = Literal[
    "repository_reference_update",
    "shared_index_projection",
    "transaction_index_write",
    "transaction_index_cleanup",
    "recovery_record_write",
    "recovery_record_cleanup",
    "descriptor_release",
    "source_compensation",
]
WorkspacePhysicalEffectState = Literal["not_attempted", "applied", "failed", "unknown"]
WorkspacePublicationFailurePhase = Literal[
    "request", "admission", "physical", "finish", "result", "cleanup"
]
WorkspaceRepositoryLockReleaseObservationRepositoryLockRelease = Literal[
    "not_acquired", "confirmed_released", "not_released", "unknown"
]
WorkspaceRepositoryWriterObservationRepositoryWritePreflight = Literal[
    "not_run", "passed", "failed"
]
WorkspaceRepositoryWriterObservationTransactionMode = Literal[
    "not_run", "shared_index_snapshot_v0", "isolated_index_atomic_ref_v1"
]
WorkspaceRepositoryWriterObservationReferenceUpdate = Literal[
    "not_run", "cas_applied", "cas_failed"
]
WorkspaceRepositoryWriterObservationSharedIndexProjection = Literal[
    "not_run", "applied", "failed"
]
WorkspaceRepositoryWriterObservationStatus = Literal["ok", "failed", "planned"]
WorkspaceRepositoryCommitResultAdmissionCompletion = Literal[
    "not_attempted", "completed", "pending", "unknown"
]


@dataclass(frozen=True, slots=True)
class WorkspaceFileIdentity:
    device: int
    inode: int


@dataclass(frozen=True, slots=True)
class WorkspaceGitCommand:
    arguments: list[str]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryCommitRequest:
    repository_ref: str
    target_paths: tuple[str, ...]
    message: str
    attempt_ref: str


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryPublicationBinding:
    binding_ref: str
    attempt_ref: str
    repository_ref: str
    publication_reference: str
    expected_head: str | None
    target_paths: tuple[str, ...]
    postimages_digest: str
    message_digest: str
    provider_generation: str
    provider_ref: str
    execution_id: str


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryPlanVerificationRequest:
    binding: WorkspaceRepositoryPublicationBinding


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryPlanVerification:
    binding: WorkspaceRepositoryPublicationBinding
    original_plan_recognized: bool
    plan_phase: str
    observation_ref: str
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryAttemptObserveRequest:
    repository_ref: str
    binding_ref: str
    attempt_ref: str
    provider_ref: str
    provider_generation: str
    execution_id: str


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryAttemptObservation:
    request: WorkspaceRepositoryAttemptObserveRequest
    observation_ref: str
    attempt_recognized: bool
    plan_observation: WorkspacePublicationPlanObservation | None
    result: WorkspaceRepositoryCommitResult | None
    lock_release: WorkspaceRepositoryLockReleaseObservation | None
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryLockReleaseObservation:
    binding_ref: str
    attempt_ref: str
    provider_ref: str
    provider_generation: str
    transaction_ref: str
    release_observation_ref: str
    repository_lock_release: (
        WorkspaceRepositoryLockReleaseObservationRepositoryLockRelease
    )
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspacePublicationCleanupObservation:
    binding_ref: str | None
    attempt_ref: str
    cleanup_state: WorkspaceCleanupState
    lock_release: WorkspaceRepositoryLockReleaseObservation | None
    ledger_complete: bool
    effects: tuple[WorkspaceRepositoryPhysicalEffect, ...]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspacePublicationPlanObservation:
    binding_ref: str | None
    attempt_ref: str
    resource_ownership: str
    cleanup_state: WorkspaceCleanupState
    ledger_complete: bool
    effects: tuple[WorkspaceRepositoryPhysicalEffect, ...]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryPhysicalEffect:
    effect_ref: str
    subject_ref: str
    kind: WorkspacePhysicalEffectKind
    state: WorkspacePhysicalEffectState
    before_ref: str | None
    after_ref: str | None
    before_digest: str | None
    after_digest: str | None
    before_identity: tuple[int, int] | None
    after_identity: tuple[int, int] | None
    mode: int | None
    durability_confirmed: bool | None
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryWriterObservation:
    repo_root: str
    issue_path: str | None
    issue_tag: str | None
    issue_owner: str | None
    issue_status: str | None
    committed_issue_blob_oid: str | None
    owner_id: str | None
    ownership_scope: list[str]
    requested_paths: list[str]
    staged_paths: list[str]
    commit_message: str | None
    commit_hash: str | None
    idempotency_ref: str | None
    request_fingerprint: str | None
    idempotent_replay: bool
    repository_write_preflight: (
        WorkspaceRepositoryWriterObservationRepositoryWritePreflight
    )
    index_restored: bool | None
    transaction_mode: WorkspaceRepositoryWriterObservationTransactionMode
    expected_head: str | None
    candidate_commit: str | None
    updated_reference: str | None
    reference_update: WorkspaceRepositoryWriterObservationReferenceUpdate
    shared_index_unchanged: bool | None
    shared_index_projection: WorkspaceRepositoryWriterObservationSharedIndexProjection
    shared_index_projection_error: str | None
    index_reconciliation_pending: bool
    repository_admission_ref: str | None
    repository_admission_evidence_digest: str | None
    dry_run: bool
    command_log: list[list[str]]
    status: WorkspaceRepositoryWriterObservationStatus
    error: str | None


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryCommitResult:
    binding_ref: str
    attempt_ref: str
    outcome: str
    publication_state: WorkspacePublicationState
    expected_head: str | None
    candidate_commit: str | None
    commit_hash: str | None
    updated_reference: str | None
    reference_update: WorkspaceReferenceUpdateState
    index_projection: WorkspaceIndexProjectionState
    cleanup_state: WorkspaceCleanupState
    lock_release: WorkspaceRepositoryLockReleaseObservation | None
    admission_completion: WorkspaceRepositoryCommitResultAdmissionCompletion
    ledger_complete: bool
    work_admission_receipt_ref: str | None
    transaction_mode: str
    shared_index_unchanged: bool | None
    index_reconciliation_pending: bool | None
    original_writer_report: WorkspaceRepositoryWriterObservation | None
    effects: tuple[WorkspaceRepositoryPhysicalEffect, ...]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryPublicationError:
    code: str
    phase: WorkspacePublicationFailurePhase
    binding_ref: str | None
    attempt_ref: str
    provider_invoked: bool
    result_validation_complete: bool
    observation: WorkspaceRepositoryCommitResult | None
    plan_observation: WorkspacePublicationPlanObservation | None
    original_cause_type: str | None
    original_cause_message: str | None
    diagnostics: tuple[str, ...]


PUBLICATION_VALUE_TYPES = (
    WorkspaceFileIdentity,
    WorkspaceGitCommand,
    WorkspaceRepositoryCommitRequest,
    WorkspaceRepositoryPublicationBinding,
    WorkspaceRepositoryPlanVerificationRequest,
    WorkspaceRepositoryPlanVerification,
    WorkspaceRepositoryAttemptObserveRequest,
    WorkspaceRepositoryAttemptObservation,
    WorkspaceRepositoryLockReleaseObservation,
    WorkspacePublicationCleanupObservation,
    WorkspacePublicationPlanObservation,
    WorkspaceRepositoryPhysicalEffect,
    WorkspaceRepositoryWriterObservation,
    WorkspaceRepositoryCommitResult,
    WorkspaceRepositoryPublicationError,
)
