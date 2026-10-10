"""Pure SDK evidence bindings for repository_delta_retention_values.aware.

Construction is descriptive, not original-owner issuance or validation. Strict
codecs validate and detach these values; no live retention facade exists here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WorkspaceRepositoryDeltaRetentionPhase = Literal[
    "allocated", "initializing", "active", "refused", "released"
]
WorkspaceRepositoryDeltaRetentionRefusalCode = Literal[
    "retention_not_issued",
    "retention_owner_mismatch",
    "retention_binding_mismatch",
    "retention_process_mismatch",
    "retention_not_active",
    "retention_initializer_spent",
    "retention_storage_initialization_refused",
    "retention_supplier_unavailable",
]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDeltaRetentionObservation:
    retention_ref: str
    repository_binding_ref: str | None
    phase: WorkspaceRepositoryDeltaRetentionPhase
    provider_generation: str
    original_process_id: int
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDeltaRetentionRefusalEvidence:
    code: WorkspaceRepositoryDeltaRetentionRefusalCode
    observation: WorkspaceRepositoryDeltaRetentionObservation | None


__all__ = (
    "WorkspaceRepositoryDeltaRetentionObservation",
    "WorkspaceRepositoryDeltaRetentionPhase",
    "WorkspaceRepositoryDeltaRetentionRefusalCode",
    "WorkspaceRepositoryDeltaRetentionRefusalEvidence",
)
