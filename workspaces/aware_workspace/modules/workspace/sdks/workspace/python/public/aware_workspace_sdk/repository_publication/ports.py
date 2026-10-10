"""Qualified descriptive port values, not executable publication ports.

Owner-local imports only. Original provider identity, spend, effects and cleanup
are runtime facts; freely constructed or decoded values cannot authenticate them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .values import (
    WorkspaceRepositoryCommitResult,
    WorkspaceRepositoryLockReleaseObservation,
    WorkspaceRepositoryPhysicalEffect,
    WorkspaceRepositoryPublicationBinding,
)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryPublicationObserveRequest:
    repository_ref: str
    publication_receipt_ref: str
    expected_binding_ref: str | None


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryPublicationObservation:
    request: WorkspaceRepositoryPublicationObserveRequest
    observation_ref: str
    provider_ref: str
    provider_generation: str
    receipt_state: Literal["present", "absent", "unknown"]
    reachability_state: Literal["reachable", "not_reachable", "unknown"]
    commit_hash: str | None
    binding: WorkspaceRepositoryPublicationBinding | None
    expected_binding_matches: bool | None
    result: WorkspaceRepositoryCommitResult | None
    ledger_complete: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryIndexReconcileRequest:
    repository_ref: str
    publication_receipt_ref: str
    target_paths: tuple[str, ...]
    attempt_ref: str
    expected_head: str | None


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryIndexReconcileResult:
    request: WorkspaceRepositoryIndexReconcileRequest
    observation_ref: str
    provider_ref: str
    provider_generation: str
    source_binding_ref: str | None
    work_admission_receipt_ref: str | None
    reconciliation_state: Literal[
        "not_attempted", "applied", "pending", "failed", "unknown"
    ]
    result: WorkspaceRepositoryCommitResult | None
    lock_release: WorkspaceRepositoryLockReleaseObservation | None
    effects: tuple[WorkspaceRepositoryPhysicalEffect, ...]
    ledger_complete: bool
    diagnostics: tuple[str, ...]


PUBLICATION_PORT_VALUE_TYPES = (
    WorkspaceRepositoryPublicationObserveRequest,
    WorkspaceRepositoryPublicationObservation,
    WorkspaceRepositoryIndexReconcileRequest,
    WorkspaceRepositoryIndexReconcileResult,
)
