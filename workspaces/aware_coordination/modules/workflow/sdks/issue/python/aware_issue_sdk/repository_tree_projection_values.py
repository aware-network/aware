"""Issue-owned tree intent and evidence. None of these values grants authority.

The runtime issues original plans/admissions/consumptions separately. The strict
codec validates descriptive shapes only; it neither checks live owners nor
selects any Workspace or FileSystem implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ISSUE_TREE_PROJECTION_OPERATION_REF = "issue_sdk.admit_repository_tree_projection"
ISSUE_TREE_PROJECTION_PROFILE = "repository_tree_projection_v1"

IssueTreePhase = Literal[
    "prepared", "admitted", "spending", "spent", "retired", "released"
]
IssueTreeConsumptionState = Literal["not_spent", "spent", "unknown"]
IssueTreeCleanupState = Literal["not_attempted", "completed", "incomplete", "unknown"]
IssueTreeResourceOwnership = Literal["owned", "borrowed", "released", "unknown"]


@dataclass(frozen=True, slots=True)
class IssueTreeProjectionRequest:
    issue_ref: str
    expected_issue_source_sha256: str
    actor_ref: str
    actor_evidence_ref: str
    client_intent_id: str
    operation_ref: str = ISSUE_TREE_PROJECTION_OPERATION_REF
    profile: str = ISSUE_TREE_PROJECTION_PROFILE


@dataclass(frozen=True, slots=True)
class IssueTreeBindingObservation:
    workspace_plan_ref: str
    workspace_provider_ref: str
    workspace_provider_generation: str
    workspace_binding_ref: str
    target_repository_binding_ref: str
    target_root_identity: tuple[int, int]
    execution_id: str
    process_id: int
    thread_id: int
    workflow_ref: str
    layout_ref: str
    source_delivery_ref: str
    physical_preparation_ref: str
    transition_sequence_digest: str
    transition_count: int
    effect_paths: tuple[str, ...]
    read_guard_paths: tuple[str, ...]
    scratch_effect_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IssueTreeAdmissionObservation:
    issue_ref: str
    request_ref: str
    binding: IssueTreeBindingObservation | None
    authority_source_path: str | None
    authority_source_digest: str | None
    authority_source_identity: tuple[int, int] | None
    authority_generation: str | None
    admission_ref: str | None
    consumption_ref: str | None
    phase: IssueTreePhase
    consumption_state: IssueTreeConsumptionState
    cleanup_state: IssueTreeCleanupState
    ledger_complete: bool
    diagnostics: tuple[str, ...]
    authorizes_retry: Literal[False] = False


@dataclass(frozen=True, slots=True)
class IssueTreeResourceCleanup:
    resource_ref: str
    kind: str
    path: str | None
    ownership: IssueTreeResourceOwnership
    cleanup_attempted: bool
    cleanup_state: IssueTreeCleanupState
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IssueTreeAdmissionCleanup:
    issue_ref: str
    request_ref: str
    admission_ref: str | None
    consumption_ref: str | None
    resources: tuple[IssueTreeResourceCleanup, ...]
    cleanup_state: IssueTreeCleanupState
    ledger_complete: bool
    diagnostics: tuple[str, ...]


__all__ = (
    "ISSUE_TREE_PROJECTION_OPERATION_REF",
    "ISSUE_TREE_PROJECTION_PROFILE",
    "IssueTreeAdmissionCleanup",
    "IssueTreeAdmissionObservation",
    "IssueTreeBindingObservation",
    "IssueTreeCleanupState",
    "IssueTreeConsumptionState",
    "IssueTreePhase",
    "IssueTreeProjectionRequest",
    "IssueTreeResourceCleanup",
    "IssueTreeResourceOwnership",
)
