"""Descriptive source metadata; native readers and bodies are not portable authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .repository_workflow_values import WorkflowCleanup, WorkspaceWorkflowMarker

MAX_WORKFLOW_SOURCE_FILES = 16384
MAX_WORKFLOW_SOURCE_BYTES = 512 * 1024 * 1024
MAX_WORKFLOW_SOURCE_METADATA_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class WorkspaceWorkflowSourceBinding:
    delivery_ref: str
    workflow_ref: str
    attempt_ref: str
    binding_ref: str
    provider_generation: str
    execution_id: str
    process_id: int
    thread_id: int
    source_repository_binding_ref: str
    target_repository_binding_ref: str
    source_repository_root: str
    target_repository_root: str
    source_root_identity: tuple[int, ...]
    target_root_identity: tuple[int, ...]
    source_commit: str
    profile_key: str
    profile_digest: str
    marker_environment: tuple[WorkspaceWorkflowMarker, ...]
    selection_digest: str
    checkout_contract: str
    output_layout_digest: str
    captured_count: int
    projected_count: int
    captured_bytes: int
    maximum_files: int
    maximum_body_bytes: int
    target_reference: str
    expected_target_head: str | None


@dataclass(frozen=True, slots=True)
class WorkspaceWorkflowSourceFile:
    source_path: str
    output_path: str
    content_digest: str
    size_bytes: int
    git_mode: Literal["100644", "100755"]
    projected_mode: Literal[420, 493]


@dataclass(frozen=True, slots=True)
class WorkspaceWorkflowSourceObservation:
    binding: WorkspaceWorkflowSourceBinding
    files: tuple[WorkspaceWorkflowSourceFile, ...]
    phase: Literal["retained"]
    cleanup_state: WorkflowCleanup


@dataclass(frozen=True, slots=True)
class WorkspaceWorkflowSourceBody:
    file: WorkspaceWorkflowSourceFile
    body: bytes


@dataclass(frozen=True, slots=True)
class WorkspaceWorkflowSourceRead:
    binding: WorkspaceWorkflowSourceBinding
    bodies: tuple[WorkspaceWorkflowSourceBody, ...]


WORKFLOW_SOURCE_VALUE_TYPES = (
    WorkspaceWorkflowMarker,
    WorkspaceWorkflowSourceBinding,
    WorkspaceWorkflowSourceFile,
    WorkspaceWorkflowSourceObservation,
)

__all__ = (
    "MAX_WORKFLOW_SOURCE_BYTES",
    "MAX_WORKFLOW_SOURCE_FILES",
    "MAX_WORKFLOW_SOURCE_METADATA_BYTES",
    "WorkspaceWorkflowSourceBinding",
    "WorkspaceWorkflowSourceBody",
    "WorkspaceWorkflowSourceFile",
    "WorkspaceWorkflowSourceObservation",
    "WorkspaceWorkflowSourceRead",
)
