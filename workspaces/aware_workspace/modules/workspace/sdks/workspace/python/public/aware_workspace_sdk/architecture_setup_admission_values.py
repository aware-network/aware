"""Workspace-owned A1 data contracts. These values confer no live authority."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from .architecture_setup import ArchitectureSetupReceipt, ArchitectureSetupRequest

ClientReleaseOutcome = Literal["not_attempted", "confirmed", "failed", "unknown"]

Confinement = Literal["descriptor_walk_v1"]

DispatchState = Literal["not_attempted", "attempted", "returned"]

DurabilityState = Literal["not_confirmed", "confirmed", "unknown"]

EffectState = Literal["none", "applied", "unknown"]

FileKind = Literal["create", "update"]

ModePolicy = Literal["legacy_kernel_umask_restore_existing_v1"]

ObservationState = Literal["not_observed", "observed", "unavailable"]

Operation = Literal[
    "repository", "workspace", "module", "python_package", "package_manager"
]

Ownership = Literal["owned", "borrowed", "released", "unknown"]

PackageOwner = Literal["repository", "workspace", "module"]

Phase = Literal[
    "preparing",
    "prepared",
    "admitted",
    "enrolled",
    "spent",
    "executing",
    "completed",
    "retired",
]

PrimaryFailureState = Literal["none", "observed", "unknown"]

ReceiptStatus = Literal["succeeded", "unchanged", "rejected", "uncertain"]

ReleaseOutcome = Literal["confirmed", "failed", "unknown"]

ResourceKind = Literal[
    "root_descriptor",
    "directory_descriptor",
    "file_descriptor",
    "scratch_descriptor",
    "lease",
    "logical_keeper",
    "temporary_buffer",
]

ScratchCleanup = Literal["original_identity_only_no_rollback"]

ScratchCollision = Literal["retire_without_reselection"]

ScratchNameSelection = Literal["prepared_once_v1"]

StepKind = Literal[
    "ancestor_create",
    "ancestor_sync",
    "scratch_create",
    "scratch_write",
    "scratch_restore_mode",
    "scratch_sync",
    "scratch_close",
    "target_link",
    "scratch_unlink",
    "target_replace",
    "parent_sync",
    "resource_release",
]


@dataclass(frozen=True, slots=True)
class WorkspaceAuthorizedSetupResult:
    binding: WorkspaceSetupPlanBinding
    original_receipt: ArchitectureSetupReceipt
    effects: tuple[WorkspaceSetupPhysicalEffect, ...]
    remaining_effects: tuple[WorkspaceSetupPhysicalStep, ...]
    scratch_residue: tuple[str, ...]
    release: ReleaseOutcome
    durability: DurabilityState
    diagnostics: tuple[str, ...]
    ledger_complete: bool
    resources: tuple[WorkspaceSetupResourceEvidence, ...]
    primary_failure: WorkspaceSetupPrimaryFailure


@dataclass(frozen=True, slots=True)
class WorkspaceSetupAncestorGuard:
    path: str
    observation: WorkspaceSetupDirectoryObservation


@dataclass(frozen=True, slots=True)
class WorkspaceSetupCleanup:
    binding: WorkspaceSetupPlanBinding | None
    phase: Phase
    resources: tuple[WorkspaceSetupResourceEvidence, ...]
    scratch_residue: tuple[str, ...]
    release: ReleaseOutcome
    diagnostics: tuple[str, ...]
    ledger_complete: bool


@dataclass(frozen=True, slots=True)
class WorkspaceSetupClientCleanup:
    provider_ref: str | None
    provider_generation: str | None
    client_ref: str | None
    resources: tuple[WorkspaceSetupResourceEvidence, ...]
    attempted: bool
    outcome: ClientReleaseOutcome
    primary_failure: WorkspaceSetupPrimaryFailure
    diagnostics: tuple[str, ...]
    ledger_complete: bool


@dataclass(frozen=True, slots=True)
class WorkspaceSetupDirectoryObservation:
    state: ObservationState
    exists: bool | None
    device: int | None
    inode: int | None
    mode: int | None
    mtime_ns: int | None
    ctime_ns: int | None


@dataclass(frozen=True, slots=True)
class WorkspaceSetupFileObservation:
    state: ObservationState
    exists: bool | None
    device: int | None
    inode: int | None
    mode: int | None
    size_bytes: int | None
    mtime_ns: int | None
    ctime_ns: int | None
    content_sha256: str | None


@dataclass(frozen=True, slots=True)
class WorkspaceSetupFileTransition:
    file_ordinal: int
    kind: FileKind
    path: str
    before: WorkspaceSetupFileObservation
    candidate_sha256: str
    candidate_size_bytes: int
    scratch_path: str
    mode_policy: ModePolicy


@dataclass(frozen=True, slots=True)
class WorkspaceSetupInputBinding:
    path: str
    observation: WorkspaceSetupFileObservation


@dataclass(frozen=True, slots=True)
class WorkspaceSetupLimits:
    ancestor_guards: int
    binding_metadata_bytes: int
    created_ancestor_paths: int
    file_bytes: int
    file_transitions: int
    input_files: int
    path_components: int
    path_utf8_bytes: int
    physical_step_count: int
    retained_before_and_after_bytes: int
    scratch_paths: int
    simultaneous_live_scratch: int
    simultaneous_owned_descriptors: int


@dataclass(frozen=True, slots=True)
class WorkspaceSetupPhysicalEffect:
    ordinal: int
    kind: StepKind
    primary_path: str
    auxiliary_paths: tuple[str, ...]
    dispatch_state: DispatchState
    effect_state: EffectState
    before: WorkspaceSetupFileObservation
    after: WorkspaceSetupFileObservation
    requested_mode: int | None
    observed_mode: int | None
    durability: DurabilityState
    original_error: str | None


@dataclass(frozen=True, slots=True)
class WorkspaceSetupPhysicalStep:
    ordinal: int
    file_ordinal: int
    kind: StepKind
    primary_path: str
    auxiliary_paths: tuple[str, ...]
    preconditions: WorkspaceSetupPreconditions
    mode_policy: ModePolicy
    requested_mode: int | None
    candidate_sha256: str
    candidate_size_bytes: int
    resource_refs: tuple[str, ...]
    cleanup_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceSetupPlanBinding:
    provider_ref: str
    provider_generation: str
    repository_root: str
    repository_identity: tuple[int, int]
    plan_ref: str
    attempt_ref: str
    operation: Operation
    request_sha256: str
    plan_sha256: str
    input_bindings: tuple[WorkspaceSetupInputBinding, ...]
    file_transitions: tuple[WorkspaceSetupFileTransition, ...]
    ancestor_guards: tuple[WorkspaceSetupAncestorGuard, ...]
    ordered_effects: tuple[WorkspaceSetupPhysicalStep, ...]
    scratch_policy: WorkspaceSetupScratchPolicy
    limits: WorkspaceSetupLimits
    physical_provider_ref: str
    physical_provider_generation: str
    physical_preparation_ref: str
    process_id: int
    thread_id: int
    confinement_profile: Confinement
    mode_policy: ModePolicy


@dataclass(frozen=True, slots=True)
class WorkspaceSetupPlanObservation:
    binding: WorkspaceSetupPlanBinding | None
    phase: Phase
    next_effect_ordinal: int
    resources: tuple[WorkspaceSetupResourceEvidence, ...]
    primary_failure: WorkspaceSetupPrimaryFailure
    ledger_complete: bool


@dataclass(frozen=True, slots=True)
class WorkspaceSetupPreconditions:
    root_identity: tuple[int, int]
    ancestor_guards: tuple[WorkspaceSetupAncestorGuard, ...]
    target: WorkspaceSetupFileObservation | None
    scratch: WorkspaceSetupFileObservation | None


@dataclass(frozen=True, slots=True)
class WorkspaceSetupPrimaryFailure:
    state: PrimaryFailureState
    owner_ref: str | None
    stage: str | None
    code: str | None
    cause_type: str | None
    interruption: bool


@dataclass(frozen=True, slots=True)
class WorkspaceSetupResourceEvidence:
    resource_ref: str
    provider_ref: str
    kind: ResourceKind
    path: str | None
    ownership: Ownership
    release_attempted: bool
    release_outcome: ReleaseOutcome
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceSetupScratchPolicy:
    name_selection: ScratchNameSelection
    collision: ScratchCollision
    cleanup: ScratchCleanup
    simultaneous_live_scratch: int


SETUP_VALUE_TYPES = (
    ArchitectureSetupRequest,
    ArchitectureSetupReceipt,
    WorkspaceAuthorizedSetupResult,
    WorkspaceSetupAncestorGuard,
    WorkspaceSetupCleanup,
    WorkspaceSetupClientCleanup,
    WorkspaceSetupDirectoryObservation,
    WorkspaceSetupFileObservation,
    WorkspaceSetupFileTransition,
    WorkspaceSetupInputBinding,
    WorkspaceSetupLimits,
    WorkspaceSetupPhysicalEffect,
    WorkspaceSetupPhysicalStep,
    WorkspaceSetupPlanBinding,
    WorkspaceSetupPlanObservation,
    WorkspaceSetupPreconditions,
    WorkspaceSetupPrimaryFailure,
    WorkspaceSetupResourceEvidence,
    WorkspaceSetupScratchPolicy,
)

SETUP_SCHEMA_IDS = MappingProxyType(
    {
        ArchitectureSetupRequest: "aware.workspace.setup-a1-original-request-view.v1",
        ArchitectureSetupReceipt: "aware.workspace.setup-a1-original-receipt-view.v1",
        WorkspaceAuthorizedSetupResult: "aware.workspace.setup-a1-result.v1",
        WorkspaceSetupAncestorGuard: "aware.workspace.setup-a1-ancestor-guard.v1",
        WorkspaceSetupCleanup: "aware.workspace.setup-a1-cleanup.v1",
        WorkspaceSetupClientCleanup: "aware.workspace.setup-a1-client-cleanup.v1",
        WorkspaceSetupDirectoryObservation: "aware.workspace.setup-a1-directory-observation.v1",
        WorkspaceSetupFileObservation: "aware.workspace.setup-a1-file-observation.v1",
        WorkspaceSetupFileTransition: "aware.workspace.setup-a1-file-transition.v1",
        WorkspaceSetupInputBinding: "aware.workspace.setup-a1-input-binding.v1",
        WorkspaceSetupLimits: "aware.workspace.setup-a1-limits.v1",
        WorkspaceSetupPhysicalEffect: "aware.workspace.setup-a1-physical-effect.v1",
        WorkspaceSetupPhysicalStep: "aware.workspace.setup-a1-physical-step.v1",
        WorkspaceSetupPlanBinding: "aware.workspace.setup-a1-plan-binding.v1",
        WorkspaceSetupPlanObservation: "aware.workspace.setup-a1-plan-observation.v1",
        WorkspaceSetupPreconditions: "aware.workspace.setup-a1-preconditions.v1",
        WorkspaceSetupPrimaryFailure: "aware.workspace.setup-a1-primary-failure.v1",
        WorkspaceSetupResourceEvidence: "aware.workspace.setup-a1-resource-evidence.v1",
        WorkspaceSetupScratchPolicy: "aware.workspace.setup-a1-scratch-policy.v1",
    }
)

SETUP_FIELD_TYPES = MappingProxyType(
    {
        ArchitectureSetupRequest: (
            ("operation", "Operation"),
            ("name", "RequestText"),
            ("workspace", "RequestText"),
            ("module", "RequestText"),
            ("path", "RequestText"),
            ("distribution", "RequestText"),
            ("import_root", "RequestText"),
            ("version", "RequestText"),
            ("requires_python", "RequestText"),
            ("dependencies", "Array[RequestText]"),
            ("license_expression", "RequestText"),
            ("owner", "PackageOwner"),
        ),
        ArchitectureSetupReceipt: (
            ("operation", "Operation"),
            ("plan_sha256", "Digest"),
            ("status", "ReceiptStatus"),
            ("written_paths", "Array[RelativePath]"),
            ("remaining_paths", "Array[RelativePath]"),
            ("diagnostics", "Array[Diagnostic]"),
        ),
        WorkspaceAuthorizedSetupResult: (
            ("binding", "WorkspaceSetupPlanBinding"),
            ("original_receipt", "ArchitectureSetupReceipt"),
            ("effects", "Array[WorkspaceSetupPhysicalEffect]"),
            ("remaining_effects", "Array[WorkspaceSetupPhysicalStep]"),
            ("scratch_residue", "Array[RelativePath]"),
            ("release", "ReleaseOutcome"),
            ("durability", "DurabilityState"),
            ("diagnostics", "Array[Diagnostic]"),
            ("ledger_complete", "Bool"),
            ("resources", "Array[WorkspaceSetupResourceEvidence]"),
            ("primary_failure", "WorkspaceSetupPrimaryFailure"),
        ),
        WorkspaceSetupAncestorGuard: (
            ("path", "RelativePath"),
            ("observation", "WorkspaceSetupDirectoryObservation"),
        ),
        WorkspaceSetupCleanup: (
            ("binding", "Nullable[WorkspaceSetupPlanBinding]"),
            ("phase", "Phase"),
            ("resources", "Array[WorkspaceSetupResourceEvidence]"),
            ("scratch_residue", "Array[RelativePath]"),
            ("release", "ReleaseOutcome"),
            ("diagnostics", "Array[Diagnostic]"),
            ("ledger_complete", "Bool"),
        ),
        WorkspaceSetupClientCleanup: (
            ("provider_ref", "Nullable[Ref]"),
            ("provider_generation", "Nullable[Ref]"),
            ("client_ref", "Nullable[Ref]"),
            ("resources", "Array[WorkspaceSetupResourceEvidence]"),
            ("attempted", "Bool"),
            ("outcome", "ClientReleaseOutcome"),
            ("primary_failure", "WorkspaceSetupPrimaryFailure"),
            ("diagnostics", "Array[Diagnostic]"),
            ("ledger_complete", "Bool"),
        ),
        WorkspaceSetupDirectoryObservation: (
            ("state", "ObservationState"),
            ("exists", "Nullable[Bool]"),
            ("device", "Nullable[U64]"),
            ("inode", "Nullable[U64]"),
            ("mode", "Nullable[U64]"),
            ("mtime_ns", "Nullable[I64]"),
            ("ctime_ns", "Nullable[I64]"),
        ),
        WorkspaceSetupFileObservation: (
            ("state", "ObservationState"),
            ("exists", "Nullable[Bool]"),
            ("device", "Nullable[U64]"),
            ("inode", "Nullable[U64]"),
            ("mode", "Nullable[U64]"),
            ("size_bytes", "Nullable[U64]"),
            ("mtime_ns", "Nullable[I64]"),
            ("ctime_ns", "Nullable[I64]"),
            ("content_sha256", "Nullable[Digest]"),
        ),
        WorkspaceSetupFileTransition: (
            ("file_ordinal", "U64"),
            ("kind", "FileKind"),
            ("path", "RelativePath"),
            ("before", "WorkspaceSetupFileObservation"),
            ("candidate_sha256", "Digest"),
            ("candidate_size_bytes", "U64"),
            ("scratch_path", "RelativePath"),
            ("mode_policy", "ModePolicy"),
        ),
        WorkspaceSetupInputBinding: (
            ("path", "RelativePath"),
            ("observation", "WorkspaceSetupFileObservation"),
        ),
        WorkspaceSetupLimits: (
            ("ancestor_guards", "U64"),
            ("binding_metadata_bytes", "U64"),
            ("created_ancestor_paths", "U64"),
            ("file_bytes", "U64"),
            ("file_transitions", "U64"),
            ("input_files", "U64"),
            ("path_components", "U64"),
            ("path_utf8_bytes", "U64"),
            ("physical_step_count", "U64"),
            ("retained_before_and_after_bytes", "U64"),
            ("scratch_paths", "U64"),
            ("simultaneous_live_scratch", "U64"),
            ("simultaneous_owned_descriptors", "U64"),
        ),
        WorkspaceSetupPhysicalEffect: (
            ("ordinal", "U64"),
            ("kind", "StepKind"),
            ("primary_path", "RelativePath"),
            ("auxiliary_paths", "Array[RelativePath]"),
            ("dispatch_state", "DispatchState"),
            ("effect_state", "EffectState"),
            ("before", "WorkspaceSetupFileObservation"),
            ("after", "WorkspaceSetupFileObservation"),
            ("requested_mode", "Nullable[U64]"),
            ("observed_mode", "Nullable[U64]"),
            ("durability", "DurabilityState"),
            ("original_error", "Nullable[Code]"),
        ),
        WorkspaceSetupPhysicalStep: (
            ("ordinal", "U64"),
            ("file_ordinal", "U64"),
            ("kind", "StepKind"),
            ("primary_path", "RelativePath"),
            ("auxiliary_paths", "Array[RelativePath]"),
            ("preconditions", "WorkspaceSetupPreconditions"),
            ("mode_policy", "ModePolicy"),
            ("requested_mode", "Nullable[U64]"),
            ("candidate_sha256", "Digest"),
            ("candidate_size_bytes", "U64"),
            ("resource_refs", "Array[Ref]"),
            ("cleanup_refs", "Array[Ref]"),
        ),
        WorkspaceSetupPlanBinding: (
            ("provider_ref", "Ref"),
            ("provider_generation", "Ref"),
            ("repository_root", "RootPath"),
            ("repository_identity", "Identity"),
            ("plan_ref", "Ref"),
            ("attempt_ref", "Ref"),
            ("operation", "Operation"),
            ("request_sha256", "Digest"),
            ("plan_sha256", "Digest"),
            ("input_bindings", "Array[WorkspaceSetupInputBinding]"),
            ("file_transitions", "Array[WorkspaceSetupFileTransition]"),
            ("ancestor_guards", "Array[WorkspaceSetupAncestorGuard]"),
            ("ordered_effects", "Array[WorkspaceSetupPhysicalStep]"),
            ("scratch_policy", "WorkspaceSetupScratchPolicy"),
            ("limits", "WorkspaceSetupLimits"),
            ("physical_provider_ref", "Ref"),
            ("physical_provider_generation", "Ref"),
            ("physical_preparation_ref", "Ref"),
            ("process_id", "U64"),
            ("thread_id", "U64"),
            ("confinement_profile", "Confinement"),
            ("mode_policy", "ModePolicy"),
        ),
        WorkspaceSetupPlanObservation: (
            ("binding", "Nullable[WorkspaceSetupPlanBinding]"),
            ("phase", "Phase"),
            ("next_effect_ordinal", "U64"),
            ("resources", "Array[WorkspaceSetupResourceEvidence]"),
            ("primary_failure", "WorkspaceSetupPrimaryFailure"),
            ("ledger_complete", "Bool"),
        ),
        WorkspaceSetupPreconditions: (
            ("root_identity", "Identity"),
            ("ancestor_guards", "Array[WorkspaceSetupAncestorGuard]"),
            ("target", "Nullable[WorkspaceSetupFileObservation]"),
            ("scratch", "Nullable[WorkspaceSetupFileObservation]"),
        ),
        WorkspaceSetupPrimaryFailure: (
            ("state", "PrimaryFailureState"),
            ("owner_ref", "Nullable[Ref]"),
            ("stage", "Nullable[Code]"),
            ("code", "Nullable[Code]"),
            ("cause_type", "Nullable[Code]"),
            ("interruption", "Bool"),
        ),
        WorkspaceSetupResourceEvidence: (
            ("resource_ref", "Ref"),
            ("provider_ref", "Ref"),
            ("kind", "ResourceKind"),
            ("path", "Nullable[ResourcePath]"),
            ("ownership", "Ownership"),
            ("release_attempted", "Bool"),
            ("release_outcome", "ReleaseOutcome"),
            ("diagnostics", "Array[Diagnostic]"),
        ),
        WorkspaceSetupScratchPolicy: (
            ("name_selection", "ScratchNameSelection"),
            ("collision", "ScratchCollision"),
            ("cleanup", "ScratchCleanup"),
            ("simultaneous_live_scratch", "U64"),
        ),
    }
)

SETUP_ENUMS = MappingProxyType(
    {
        "ClientReleaseOutcome": ("not_attempted", "confirmed", "failed", "unknown"),
        "Confinement": ("descriptor_walk_v1",),
        "DispatchState": ("not_attempted", "attempted", "returned"),
        "DurabilityState": ("not_confirmed", "confirmed", "unknown"),
        "EffectState": ("none", "applied", "unknown"),
        "FileKind": ("create", "update"),
        "ModePolicy": ("legacy_kernel_umask_restore_existing_v1",),
        "ObservationState": ("not_observed", "observed", "unavailable"),
        "Operation": (
            "repository",
            "workspace",
            "module",
            "python_package",
            "package_manager",
        ),
        "Ownership": ("owned", "borrowed", "released", "unknown"),
        "PackageOwner": ("repository", "workspace", "module"),
        "Phase": (
            "preparing",
            "prepared",
            "admitted",
            "enrolled",
            "spent",
            "executing",
            "completed",
            "retired",
        ),
        "PrimaryFailureState": ("none", "observed", "unknown"),
        "ReceiptStatus": ("succeeded", "unchanged", "rejected", "uncertain"),
        "ReleaseOutcome": ("confirmed", "failed", "unknown"),
        "ResourceKind": (
            "root_descriptor",
            "directory_descriptor",
            "file_descriptor",
            "scratch_descriptor",
            "lease",
            "logical_keeper",
            "temporary_buffer",
        ),
        "ScratchCleanup": ("original_identity_only_no_rollback",),
        "ScratchCollision": ("retire_without_reselection",),
        "ScratchNameSelection": ("prepared_once_v1",),
        "StepKind": (
            "ancestor_create",
            "ancestor_sync",
            "scratch_create",
            "scratch_write",
            "scratch_restore_mode",
            "scratch_sync",
            "scratch_close",
            "target_link",
            "scratch_unlink",
            "target_replace",
            "parent_sync",
            "resource_release",
        ),
    }
)

WORKSPACE_SETUP_LIMIT_CAPS = MappingProxyType(
    {
        "ancestor_guards": 4096,
        "binding_metadata_bytes": 2097152,
        "created_ancestor_paths": 1024,
        "file_bytes": 1048576,
        "file_transitions": 1024,
        "input_files": 4096,
        "path_components": 64,
        "path_utf8_bytes": 1024,
        "physical_step_count": 12288,
        "retained_before_and_after_bytes": 31457280,
        "scratch_paths": 1024,
        "simultaneous_live_scratch": 1,
        "simultaneous_owned_descriptors": 80,
    }
)
