"""Legacy value coordinates only; physical storage belongs to Workspace FS."""

from .repository_delta_store_contract import (
    DEFAULT_DELTA_BODY_BYTES,
    DEFAULT_DELTA_BODY_CAPACITY,
    DEFAULT_DELTA_CAPTURE_CAPACITY,
    DEFAULT_DELTA_TRANSITION_CAPACITY,
    MAX_DELTA_BODY_BYTES,
    MAX_DELTA_BODY_CAPACITY,
    MAX_DELTA_CAPTURE_CAPACITY,
    MAX_DELTA_TRANSITION_CAPACITY,
    WORKSPACE_REPOSITORY_DELTA_STORE_CONTRACT_REF,
    WORKSPACE_REPOSITORY_DELTA_STORE_VERSION,
    WorkspaceRepositoryDeltaStoreCapacityError,
    WorkspaceRepositoryDeltaStoreCorrupt,
    WorkspaceRepositoryDeltaStoreError,
    WorkspaceRepositoryDeltaStoreMetrics,
    WorkspaceRepositoryDeltaStoreSnapshot,
)

__all__ = (
    "DEFAULT_DELTA_BODY_BYTES",
    "DEFAULT_DELTA_BODY_CAPACITY",
    "DEFAULT_DELTA_CAPTURE_CAPACITY",
    "DEFAULT_DELTA_TRANSITION_CAPACITY",
    "MAX_DELTA_BODY_BYTES",
    "MAX_DELTA_BODY_CAPACITY",
    "MAX_DELTA_CAPTURE_CAPACITY",
    "MAX_DELTA_TRANSITION_CAPACITY",
    "WORKSPACE_REPOSITORY_DELTA_STORE_CONTRACT_REF",
    "WORKSPACE_REPOSITORY_DELTA_STORE_VERSION",
    "WorkspaceRepositoryDeltaStoreCapacityError",
    "WorkspaceRepositoryDeltaStoreCorrupt",
    "WorkspaceRepositoryDeltaStoreError",
    "WorkspaceRepositoryDeltaStoreMetrics",
    "WorkspaceRepositoryDeltaStoreSnapshot",
)
