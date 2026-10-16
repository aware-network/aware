"""Closed descriptive tree values. Construction does not issue live authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .repository_source_projection_values import RepositoryObservationCoordinate
from .repository_workflow_source_values import WorkspaceWorkflowSourceBinding

TreeKind = Literal["CREATE", "UPDATE", "DELETE"]

AncestorIntent = Literal["create", "preserve"]

ConfinementProfile = Literal["descriptor_walk_v1"]

ScratchRole = Literal["replacement_body"]

ScratchKind = Literal["create", "mode", "unlink", "sync"]

PlanPhase = Literal["prepared", "enrolled", "spending", "spent", "held", "released"]

ResultPhase = Literal["prepared", "partial", "complete", "held", "released"]

TransitionKind = Literal[
    "CREATE", "UPDATE", "DELETE", "directory_create", "directory_preserve"
]

PhysicalEffectKind = Literal[
    "directory_create",
    "file_create",
    "file_replace",
    "file_delete",
    "mode_update",
    "scratch_create",
    "scratch_unlink",
    "directory_sync",
    "file_sync",
    "descriptor_release",
]

EffectState = Literal["none", "applied", "unknown"]

CompletionState = Literal["not_started", "partial", "complete", "unknown"]

ConvergenceState = Literal["not_verified", "matched", "mismatched", "unknown"]

RetentionState = Literal["not_attempted", "retained", "unavailable", "unknown"]

IndexState = Literal["not_attempted", "persisted", "unavailable", "unknown"]

ResourceOwnership = Literal["owned", "borrowed", "released", "unknown"]

CleanupState = Literal["not_attempted", "completed", "incomplete", "unknown"]

VerificationState = Literal["not_attempted", "verified", "refused", "unknown"]

ResolutionState = Literal["known", "incomplete", "unknown", "historical_descriptive"]

RefusalCode = Literal[
    "malformed_request",
    "source_unavailable",
    "stale_source",
    "stale_target",
    "target_authority_mismatch",
    "quota_exceeded",
    "issue_unavailable",
    "issue_refused",
    "physical_unavailable",
    "physical_refused",
    "original_owner_required",
    "retired",
    "unsupported_profile",
    "retention_unavailable",
    "index_unavailable",
    "cleanup_unknown",
]


@dataclass(frozen=True, slots=True)
class WorkspaceTreeFileIntent:
    path: str
    kind: TreeKind
    source_output_path: str | None
    requested_mode: int | None


@dataclass(frozen=True, slots=True)
class WorkspaceTreeAncestorIntent:
    path: str
    intent: AncestorIntent
    requested_mode: int | None


@dataclass(frozen=True, slots=True)
class WorkspaceTreeProjectionRequest:
    workflow_ref: str
    layout_ref: str
    invocation_ref: str
    expected_source_binding: WorkspaceWorkflowSourceBinding
    files: tuple[WorkspaceTreeFileIntent, ...]
    ancestors: tuple[WorkspaceTreeAncestorIntent, ...]
    confinement_profile: ConfinementProfile
    limits: WorkspaceTreeLimits


@dataclass(frozen=True, slots=True)
class WorkspaceTreeLimits:
    maximum_file_transitions: int
    maximum_ancestors: int
    maximum_file_bytes: int
    maximum_combined_body_bytes: int
    maximum_metadata_bytes: int
    maximum_path_utf8_bytes: int
    maximum_live_descriptors: int
    maximum_retained_bodies: int
    maximum_retained_captures: int
    maximum_retained_deltas: int


@dataclass(frozen=True, slots=True)
class WorkspaceTreeEntryPin:
    exists: bool
    device: int | None
    inode: int | None
    size_bytes: int | None
    mtime_ns: int | None
    ctime_ns: int | None
    mode: int | None
    link_count: int | None
    content_digest: str | None


@dataclass(frozen=True, slots=True)
class WorkspaceTreeFileTransition:
    path: str
    kind: TreeKind
    source_output_path: str | None
    source_path: str | None
    before: WorkspaceTreeEntryPin
    before_body_ref: str | None
    successor_body_ref: str | None
    successor_digest: str | None
    successor_size_bytes: int | None
    requested_mode: int | None


@dataclass(frozen=True, slots=True)
class WorkspaceTreeAncestorTransition:
    path: str
    intent: AncestorIntent
    before: WorkspaceTreeEntryPin
    requested_mode: int | None


@dataclass(frozen=True, slots=True)
class WorkspaceTreeScratchEffect:
    path: str
    role: ScratchRole
    ordinal: int
    kind: ScratchKind
    requested_mode: int | None


@dataclass(frozen=True, slots=True)
class WorkspaceTreeProjectionBinding:
    plan_ref: str
    provider_ref: str
    provider_generation: str
    execution_id: str
    process_id: int
    thread_id: int
    target_repository_binding_ref: str
    target_root_identity: tuple[int, ...]
    source_binding: WorkspaceWorkflowSourceBinding
    observation_coordinate: RepositoryObservationCoordinate
    workflow_ref: str
    layout_ref: str
    invocation_ref: str
    request_digest: str
    physical_preparation_ref: str
    physical_request_ref: str
    physical_request_digest: str
    transition_sequence_digest: str
    transition_count: int
    files: tuple[WorkspaceTreeFileTransition, ...]
    ancestors: tuple[WorkspaceTreeAncestorTransition, ...]
    scratch_effects: tuple[WorkspaceTreeScratchEffect, ...]
    effect_paths: tuple[str, ...]
    read_guard_paths: tuple[str, ...]
    limits: WorkspaceTreeLimits
    binding_ref: str


@dataclass(frozen=True, slots=True)
class WorkspaceTreeProjectionPlanObservation:
    binding: WorkspaceTreeProjectionBinding
    phase: PlanPhase
    cleanup: WorkspaceTreeProjectionCleanupObservation
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceTreePhysicalEffect:
    effect_ref: str
    ordinal: int
    path: str
    role: str
    kind: PhysicalEffectKind
    state: EffectState
    before_identity: tuple[int, ...] | None
    after_identity: tuple[int, ...] | None
    before_digest: str | None
    after_digest: str | None
    before_size_bytes: int | None
    after_size_bytes: int | None
    before_mode: int | None
    after_mode: int | None
    durability_confirmed: bool
    error_ref: str | None


@dataclass(frozen=True, slots=True)
class WorkspaceTreeTransitionReceipt:
    binding_ref: str
    invocation_ref: str
    consumption_ref: str
    physical_preparation_ref: str
    ordinal: int
    path: str
    kind: TransitionKind
    physical_effects: tuple[WorkspaceTreePhysicalEffect, ...]
    before: WorkspaceTreeEntryPin
    after: WorkspaceTreeEntryPin | None
    mutation_receipt_ref: str | None
    capture_ref: str | None
    delta_ref: str | None
    effect_state: EffectState
    completion_state: CompletionState
    durability_confirmed: bool
    convergence_state: ConvergenceState
    body_retention_state: RetentionState
    index_state: IndexState
    error_refs: tuple[str, ...]
    cleanup: WorkspaceTreeProjectionCleanupObservation


@dataclass(frozen=True, slots=True)
class WorkspaceTreeResourceCleanup:
    resource_ref: str
    kind: str
    path: str | None
    ownership: ResourceOwnership
    cleanup_attempted: bool
    cleanup_state: CleanupState
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceTreeProjectionCleanupObservation:
    binding_ref: str | None
    resources: tuple[WorkspaceTreeResourceCleanup, ...]
    residual_scratch: tuple[str, ...]
    cleanup_state: CleanupState
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceTreeProjectionObservation:
    result_ref: str
    binding: WorkspaceTreeProjectionBinding
    consumption_ref: str | None
    receipts: tuple[WorkspaceTreeTransitionReceipt, ...]
    completed_prefix: int
    pending_ordinal: int | None
    phase: ResultPhase
    final_entries: tuple[WorkspaceTreeEntryPin, ...]
    source_verification_state: VerificationState
    mode_verification_state: VerificationState
    ancestor_verification_state: VerificationState
    body_retention_state: RetentionState
    index_state: IndexState
    effect_state: EffectState
    cleanup: WorkspaceTreeProjectionCleanupObservation
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceTreeProjectionResolution:
    observation: WorkspaceTreeProjectionObservation
    resolution_state: ResolutionState
    authorizes_retry: bool


@dataclass(frozen=True, slots=True)
class WorkspaceTreeProjectionRefusalEvidence:
    code: RefusalCode
    observation: WorkspaceTreeProjectionObservation | None
    cleanup: WorkspaceTreeProjectionCleanupObservation
    diagnostics: tuple[str, ...]
    authorizes_retry: bool


TREE_SCHEMA_IDS = {
    WorkspaceTreeFileIntent: "aware.workspace.tree-file-intent.v1",
    WorkspaceTreeAncestorIntent: "aware.workspace.tree-ancestor-intent.v1",
    WorkspaceTreeProjectionRequest: "aware.workspace.tree-projection-request.v1",
    WorkspaceTreeLimits: "aware.workspace.tree-limits.v1",
    WorkspaceTreeEntryPin: "aware.workspace.tree-entry-pin.v1",
    WorkspaceTreeFileTransition: "aware.workspace.tree-file-transition.v1",
    WorkspaceTreeAncestorTransition: "aware.workspace.tree-ancestor-transition.v1",
    WorkspaceTreeScratchEffect: "aware.workspace.tree-scratch-effect.v1",
    WorkspaceTreeProjectionBinding: "aware.workspace.tree-projection-binding.v1",
    WorkspaceTreeProjectionPlanObservation: "aware.workspace.tree-projection-plan-observation.v1",
    WorkspaceTreePhysicalEffect: "aware.workspace.tree-physical-effect.v1",
    WorkspaceTreeTransitionReceipt: "aware.workspace.tree-transition-receipt.v1",
    WorkspaceTreeResourceCleanup: "aware.workspace.tree-resource-cleanup.v1",
    WorkspaceTreeProjectionCleanupObservation: "aware.workspace.tree-projection-cleanup-observation.v1",
    WorkspaceTreeProjectionObservation: "aware.workspace.tree-projection-observation.v1",
    WorkspaceTreeProjectionResolution: "aware.workspace.tree-projection-resolution.v1",
    WorkspaceTreeProjectionRefusalEvidence: "aware.workspace.tree-projection-refusal-evidence.v1",
}

TREE_VALUE_TYPES = (
    WorkspaceTreeFileIntent,
    WorkspaceTreeAncestorIntent,
    WorkspaceTreeProjectionRequest,
    WorkspaceTreeLimits,
    WorkspaceTreeEntryPin,
    WorkspaceTreeFileTransition,
    WorkspaceTreeAncestorTransition,
    WorkspaceTreeScratchEffect,
    WorkspaceTreeProjectionBinding,
    WorkspaceTreeProjectionPlanObservation,
    WorkspaceTreePhysicalEffect,
    WorkspaceTreeTransitionReceipt,
    WorkspaceTreeResourceCleanup,
    WorkspaceTreeProjectionCleanupObservation,
    WorkspaceTreeProjectionObservation,
    WorkspaceTreeProjectionResolution,
    WorkspaceTreeProjectionRefusalEvidence,
)

TREE_PROFILE = "repository_tree_projection_v1"
TREE_PURPOSE = "aware.workspace.repository-tree-projection.v1"
MAX_TREE_FILES = 4096
MAX_TREE_ANCESTORS = 4096
MAX_TREE_FILE_BYTES = 16 * 1024 * 1024
MAX_TREE_COMBINED_BODY_BYTES = 512 * 1024 * 1024
MAX_TREE_METADATA_BYTES = 8 * 1024 * 1024
MAX_TREE_PATH_BYTES = 1024
MAX_TREE_DESCRIPTORS = 64
MAX_TREE_BODIES = 4096
MAX_TREE_CAPTURES = 1024
MAX_TREE_DELTAS = 4096
MAX_TREE_RECEIPTS = 8192
MAX_TREE_SUBEFFECTS = 16

DEFAULT_TREE_LIMITS = WorkspaceTreeLimits(
    MAX_TREE_FILES,
    MAX_TREE_ANCESTORS,
    MAX_TREE_FILE_BYTES,
    MAX_TREE_COMBINED_BODY_BYTES,
    MAX_TREE_METADATA_BYTES,
    MAX_TREE_PATH_BYTES,
    MAX_TREE_DESCRIPTORS,
    MAX_TREE_BODIES,
    MAX_TREE_CAPTURES,
    MAX_TREE_DELTAS,
)


@dataclass(frozen=True, slots=True)
class WorkspaceTreeTargetRead:
    """Native adapter delivery; excluded from all portable value registries."""

    entry: WorkspaceTreeEntryPin
    root_identity: tuple[int, ...]
    body: bytes | None
