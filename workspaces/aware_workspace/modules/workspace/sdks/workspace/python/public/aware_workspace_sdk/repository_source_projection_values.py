"""Pure descriptive bindings for repository_source_projection_values.aware.

No provider selection, runtime evaluation, IO or serializable live handles.
The source effect mirror has a distinct name from Git-publication evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WorkspaceSourceProjectionPhase = Literal[
    "prepared", "enrolled", "spent", "terminal", "retired"
]
WorkspaceSourcePhysicalEffectState = Literal["none", "applied", "unknown"]
WorkspaceSourcePhysicalReturnState = Literal[
    "not_dispatched", "returned", "unavailable"
]
WorkspaceSourceBodyRetentionState = Literal["not_attempted", "retained", "unknown"]
WorkspaceSourceConvergenceState = Literal[
    "not_attempted", "converged", "failed", "unknown"
]
WorkspaceSourceRetentionState = Literal[
    "not_attempted", "retained", "unavailable", "unknown"
]
WorkspaceSourceCleanupState = Literal[
    "not_attempted", "completed", "incomplete", "unknown"
]
WorkspaceSourcePhysicalGuarantee = Literal["descriptor_walk_v1", "continuous_root_v1"]


@dataclass(frozen=True, slots=True)
class RepositoryObservationCoordinate:
    repository_binding_ref: str
    epoch: str
    cursor: int
    snapshot_digest: str
    visibility_policy_ref: str
    visibility_policy_version: str


@dataclass(frozen=True, slots=True)
class WorkspaceSourcePhysicalEffect:
    state: WorkspaceSourcePhysicalEffectState
    durability_confirmed: bool
    before_exists: bool
    before_content_digest: str | None
    before_size_bytes: int | None
    after_exists: bool
    after_content_digest: str | None
    after_size_bytes: int | None


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryMutationExecutionEvidence:
    physical_return_state: WorkspaceSourcePhysicalReturnState
    body_retention_state: WorkspaceSourceBodyRetentionState
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceSourceProviderBinding:
    provider_ref: str
    provider_generation: str
    execution_id: str
    original_process_id: int
    original_thread_id: int


@dataclass(frozen=True, slots=True)
class WorkspaceSourceFileIdentity:
    device: int
    inode: int


@dataclass(frozen=True, slots=True)
class WorkspaceSourceObservation:
    observation_ref: str
    provider: WorkspaceSourceProviderBinding
    repository_binding_ref: str
    target_path: str
    root_identity: WorkspaceSourceFileIdentity
    target_identity: WorkspaceSourceFileIdentity
    coordinate: RepositoryObservationCoordinate
    content_digest: str
    size_bytes: int
    body_ref: str


@dataclass(frozen=True, slots=True)
class WorkspaceSourceProjectionRequest:
    source: WorkspaceSourceObservation
    operation_ref: str
    domain_target_ref: str
    profile_ref: str
    projected_content_digest: str
    projected_size_bytes: int
    projected_body_ref: str
    physical_guarantee: WorkspaceSourcePhysicalGuarantee


@dataclass(frozen=True, slots=True)
class WorkspaceSourceProjectionBinding:
    binding_ref: str
    attempt_ref: str
    provider: WorkspaceSourceProviderBinding
    operation_ref: str
    domain_target_ref: str
    profile_ref: str
    source_observation_ref: str
    repository_binding_ref: str
    target_path: str
    root_identity: WorkspaceSourceFileIdentity
    target_identity: WorkspaceSourceFileIdentity
    expected_coordinate: RepositoryObservationCoordinate
    expected_content_digest: str
    projected_content_digest: str
    projected_size_bytes: int
    preimage_body_ref: str
    projected_body_ref: str
    physical_guarantee: WorkspaceSourcePhysicalGuarantee


@dataclass(frozen=True, slots=True)
class WorkspaceSourceProjectionPlanObservation:
    binding: WorkspaceSourceProjectionBinding
    phase: WorkspaceSourceProjectionPhase
    original_plan_recognized: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceSourceProjectionRetentionObservation:
    state: WorkspaceSourceRetentionState
    retention_ref: str | None
    preimage_body_ref: str | None
    postimage_body_ref: str | None
    capture_ref: str | None
    content_delta_ref: str | None
    before_coordinate: RepositoryObservationCoordinate | None
    after_coordinate: RepositoryObservationCoordinate | None
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceSourceProjectionCleanupObservation:
    state: WorkspaceSourceCleanupState
    observer_cleanup_state: WorkspaceSourceCleanupState
    retention_cleanup_state: WorkspaceSourceCleanupState
    physical_cleanup_state: WorkspaceSourceCleanupState
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceSourceProjectionObservation:
    binding: WorkspaceSourceProjectionBinding
    phase: WorkspaceSourceProjectionPhase
    source_effect_state: WorkspaceSourcePhysicalEffectState
    mutation_receipt_ref: str | None
    physical_effect: WorkspaceSourcePhysicalEffect | None
    execution_evidence: WorkspaceRepositoryMutationExecutionEvidence | None
    convergence_state: WorkspaceSourceConvergenceState
    retention: WorkspaceSourceProjectionRetentionObservation
    cleanup: WorkspaceSourceProjectionCleanupObservation
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceSourceProjectionRefusalEvidence:
    code: str
    observation: WorkspaceSourceProjectionObservation | None
    cleanup: WorkspaceSourceProjectionCleanupObservation | None
    ledger_complete: bool
    diagnostics: tuple[str, ...]


SOURCE_PROJECTION_VALUE_TYPES = (
    RepositoryObservationCoordinate,
    WorkspaceSourcePhysicalEffect,
    WorkspaceRepositoryMutationExecutionEvidence,
    WorkspaceSourceProviderBinding,
    WorkspaceSourceFileIdentity,
    WorkspaceSourceObservation,
    WorkspaceSourceProjectionRequest,
    WorkspaceSourceProjectionBinding,
    WorkspaceSourceProjectionPlanObservation,
    WorkspaceSourceProjectionRetentionObservation,
    WorkspaceSourceProjectionCleanupObservation,
    WorkspaceSourceProjectionObservation,
    WorkspaceSourceProjectionRefusalEvidence,
)

__all__ = (
    "SOURCE_PROJECTION_VALUE_TYPES",
    "RepositoryObservationCoordinate",
    "WorkspaceRepositoryMutationExecutionEvidence",
    "WorkspaceSourceBodyRetentionState",
    "WorkspaceSourceCleanupState",
    "WorkspaceSourceConvergenceState",
    "WorkspaceSourceFileIdentity",
    "WorkspaceSourceObservation",
    "WorkspaceSourcePhysicalEffect",
    "WorkspaceSourcePhysicalEffectState",
    "WorkspaceSourcePhysicalGuarantee",
    "WorkspaceSourcePhysicalReturnState",
    "WorkspaceSourceProjectionBinding",
    "WorkspaceSourceProjectionCleanupObservation",
    "WorkspaceSourceProjectionObservation",
    "WorkspaceSourceProjectionPhase",
    "WorkspaceSourceProjectionPlanObservation",
    "WorkspaceSourceProjectionRefusalEvidence",
    "WorkspaceSourceProjectionRequest",
    "WorkspaceSourceProjectionRetentionObservation",
    "WorkspaceSourceProviderBinding",
    "WorkspaceSourceRetentionState",
)
