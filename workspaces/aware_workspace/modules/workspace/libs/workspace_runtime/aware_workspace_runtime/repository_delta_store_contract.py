"""Neutral delta-store evidence and limits, not a storage capability."""

from __future__ import annotations

from dataclasses import dataclass

WORKSPACE_REPOSITORY_DELTA_STORE_CONTRACT_REF = (
    "aware.workspace.repository-delta-store.v1"
)
WORKSPACE_REPOSITORY_DELTA_STORE_VERSION = "1"

DEFAULT_DELTA_BODY_CAPACITY = 256
MAX_DELTA_BODY_CAPACITY = 4096
DEFAULT_DELTA_BODY_BYTES = 64 * 1024 * 1024
MAX_DELTA_BODY_BYTES = 512 * 1024 * 1024
DEFAULT_DELTA_CAPTURE_CAPACITY = 64
MAX_DELTA_CAPTURE_CAPACITY = 1024
DEFAULT_DELTA_TRANSITION_CAPACITY = 256
MAX_DELTA_TRANSITION_CAPACITY = 4096


class WorkspaceRepositoryDeltaStoreError(RuntimeError):
    pass


class WorkspaceRepositoryDeltaStoreCapacityError(WorkspaceRepositoryDeltaStoreError):
    pass


class WorkspaceRepositoryDeltaStoreCorrupt(WorkspaceRepositoryDeltaStoreError):
    pass


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDeltaStoreMetrics:
    body_hash_count: int
    body_read_count: int
    body_read_bytes: int
    body_write_count: int
    body_write_bytes: int
    index_write_count: int
    evicted_body_count: int
    evicted_capture_count: int
    evicted_delta_count: int


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryDeltaStoreSnapshot:
    repository_binding_ref: str
    retained_body_count: int
    retained_body_bytes: int
    retained_capture_count: int
    retained_delta_count: int
    metrics: WorkspaceRepositoryDeltaStoreMetrics
