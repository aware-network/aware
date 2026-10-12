"""Authored descriptive bindings; values never restore an original admission."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WorkflowStage = Literal[
    "source_capture",
    "qualification",
    "envelope",
    "tree_projection",
    "local_publication",
    "selection_freeze",
    "remote_delivery",
    "acquisition",
    "evidence_closeout",
]
WorkflowPersistence = Literal["not_written", "persisted", "unknown"]
WorkflowCleanup = Literal["not_attempted", "completed", "incomplete", "unknown"]
WorkflowEffect = Literal["none", "applied", "unknown"]
WorkflowAvailability = Literal["available", "supplier_unavailable"]
WorkflowArtifactKind = Literal[
    "candidate",
    "envelope",
    "layout",
    "instructions",
    "selection",
    "freeze",
    "acquisition",
]
WorkflowEvidenceGrade = Literal["owner_observed", "caller_reported"]
WorkflowDispatch = Literal["not_dispatched", "returned", "unavailable"]
WorkflowIntegrity = Literal["verified", "incomplete", "corrupt", "unknown"]
WorkflowAuthority = Literal["descriptive_only"]
WorkflowRefusalCode = Literal[
    "malformed_binding",
    "stale_source",
    "stale_target",
    "source_unavailable",
    "issue_admission_unavailable",
    "projection_capability_unavailable",
    "evidence_conflict",
    "evidence_corrupt",
    "evidence_persistence_unknown",
    "foreign_or_retired_handle",
    "supplier_unavailable",
]


@dataclass(frozen=True, slots=True)
class WorkspaceWorkflowMarker:
    key: str
    value: str


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryWorkflowRequest:
    workflow_ref: str
    attempt_ref: str
    source_commit: str
    profile_key: str
    profile_digest: str
    marker_environment: tuple[WorkspaceWorkflowMarker, ...]
    target_reference: str
    expected_target_head: str | None


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryWorkflowStageObservation:
    stage: WorkflowStage
    availability: WorkflowAvailability
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryWorkflowPlanObservation:
    binding_ref: str
    source_repository_binding_ref: str
    target_repository_binding_ref: str
    source_commit: str
    profile_key: str
    profile_digest: str
    selection_digest: str
    target_reference: str
    expected_target_head: str | None
    stages: tuple[WorkspaceRepositoryWorkflowStageObservation, ...]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryWorkflowArtifactBinding:
    kind: WorkflowArtifactKind
    coordinate: str
    sha256: str
    size_bytes: int
    owner_ref: str
    receipt_ref: str


@dataclass(frozen=True, slots=True)
class WorkspaceWorkflowEvidenceReference:
    owner_ref: str
    coordinate: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryWorkflowEvidenceAppendRequest:
    attempt_binding_ref: str
    expected_cursor: int
    expected_previous_digest: str
    stage: WorkflowStage
    invocation_ref: str
    artifact_bindings: tuple[WorkspaceRepositoryWorkflowArtifactBinding, ...]
    request_refs: tuple[WorkspaceWorkflowEvidenceReference, ...]
    result_refs: tuple[WorkspaceWorkflowEvidenceReference, ...]
    error_refs: tuple[WorkspaceWorkflowEvidenceReference, ...]
    evidence_grade: WorkflowEvidenceGrade
    dispatch_state: WorkflowDispatch
    effect_state: WorkflowEffect
    cleanup_state: WorkflowCleanup
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryWorkflowEvidenceWriteObservation:
    attempt_binding_ref: str
    prior_cursor: int
    observed_cursor: int | None
    prior_digest: str
    observed_digest: str | None
    persistence_state: WorkflowPersistence
    owner_observations: tuple[WorkspaceWorkflowEvidenceReference, ...]
    effect_state: WorkflowEffect
    cleanup_state: WorkflowCleanup
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryWorkflowAttemptObserveRequest:
    source_repository_binding_ref: str
    target_repository_binding_ref: str
    attempt_ref: str
    expected_binding_digest: str


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryWorkflowAttemptObservation:
    plan: WorkspaceRepositoryWorkflowPlanObservation
    records: tuple[WorkspaceRepositoryWorkflowEvidenceAppendRequest, ...]
    last_verified_cursor: int
    last_verified_digest: str
    persistence_state: WorkflowPersistence
    integrity_state: WorkflowIntegrity
    cleanup_state: WorkflowCleanup
    authority_state: WorkflowAuthority
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryWorkflowCleanupObservation:
    attempt_binding_ref: str | None
    state: WorkflowCleanup
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryWorkflowRefusalEvidence:
    code: WorkflowRefusalCode
    stage: WorkflowStage
    original_evidence_refs: tuple[WorkspaceWorkflowEvidenceReference, ...]
    persistence_state: WorkflowPersistence
    cleanup: WorkspaceRepositoryWorkflowCleanupObservation
    diagnostics: tuple[str, ...]


WORKFLOW_VALUE_TYPES = (
    WorkspaceWorkflowMarker,
    WorkspaceRepositoryWorkflowRequest,
    WorkspaceRepositoryWorkflowStageObservation,
    WorkspaceRepositoryWorkflowPlanObservation,
    WorkspaceRepositoryWorkflowArtifactBinding,
    WorkspaceWorkflowEvidenceReference,
    WorkspaceRepositoryWorkflowEvidenceAppendRequest,
    WorkspaceRepositoryWorkflowEvidenceWriteObservation,
    WorkspaceRepositoryWorkflowAttemptObserveRequest,
    WorkspaceRepositoryWorkflowAttemptObservation,
    WorkspaceRepositoryWorkflowCleanupObservation,
    WorkspaceRepositoryWorkflowRefusalEvidence,
)

__all__ = (
    "WORKFLOW_VALUE_TYPES",
    "WorkflowArtifactKind",
    "WorkflowAuthority",
    "WorkflowAvailability",
    "WorkflowCleanup",
    "WorkflowDispatch",
    "WorkflowEffect",
    "WorkflowEvidenceGrade",
    "WorkflowIntegrity",
    "WorkflowPersistence",
    "WorkflowRefusalCode",
    "WorkflowStage",
    "WorkspaceRepositoryWorkflowArtifactBinding",
    "WorkspaceRepositoryWorkflowAttemptObservation",
    "WorkspaceRepositoryWorkflowAttemptObserveRequest",
    "WorkspaceRepositoryWorkflowCleanupObservation",
    "WorkspaceRepositoryWorkflowEvidenceAppendRequest",
    "WorkspaceRepositoryWorkflowEvidenceWriteObservation",
    "WorkspaceRepositoryWorkflowPlanObservation",
    "WorkspaceRepositoryWorkflowRefusalEvidence",
    "WorkspaceRepositoryWorkflowRequest",
    "WorkspaceRepositoryWorkflowStageObservation",
    "WorkspaceWorkflowEvidenceReference",
    "WorkspaceWorkflowMarker",
)
