from __future__ import annotations

from aware_meta_ontology.class_.class_instance import ClassInstance

from aware_meta.graph.instance.commit.contract import (
    CommitActionDescriptor,
    CommitEnvelopeReader,
    JsonObject,
    LaneCommitBackend,
    LaneCommitStore,
    LaneCommitter,
    LaneHeadCommitReceipt,
    LaneHeadWatcher,
    ObjectInstanceGraphCommitBodyRecord,
    ObjectInstanceGraphCommitEnvelope,
    ObjectInstanceGraphCommitGraphHashSource,
    ObjectInstanceGraphCommitHealthMetadata,
    ObjectInstanceGraphCommitIdentityMetadata,
    ObjectInstanceGraphCommitIdentitySidecar,
    ObjectInstanceGraphCommitPreStateEvidence,
    ObjectInstanceGraphCommitRef,
    ObjectInstanceGraphCommitRootMetadata,
    ObjectInstanceGraphSnapshotHealthMetadata,
    OigiHistoryDomainCommitProjection,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_runtime_state import (
    _SESSION_JSON_FILE_CACHE,
    _clear_fs_store_session_read_cache_for_tests as _runtime_clear_fs_store_session_read_cache_for_tests,
    _snapshot_fs_store_session_read_cache_metrics as _runtime_snapshot_fs_store_session_read_cache_metrics,
)
from aware_meta.graph.instance.commit.fs_snapshot_store import (
    FSSnapshotStore,
)
from aware_meta.graph.instance.commit.snapshot_state_rows import (
    ObjectInstanceGraphSnapshotStateSelection,
    _commit_state_rows_from_snapshot_payload,
    _commit_state_rows_read_from_snapshot_payload,
    _snapshot_state_rows_payload_hash,
    _snapshot_state_rows_payload_write,
)
from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    CommitStateRow,
)
from aware_meta.graph.instance.commit.state_snapshot_segments import (
    ObjectInstanceGraphSnapshotStateClassSegment,
    ObjectInstanceGraphSnapshotStateClassSegmentSelection,
    ObjectInstanceGraphSnapshotStateRawClassSegment,
    ObjectInstanceGraphSnapshotStateRawClassSegmentIndexSelection,
    ObjectInstanceGraphSnapshotStateRawClassSegmentSelection,
    ObjectInstanceGraphSnapshotStateSegmentIndexMetadata,
    ObjectInstanceGraphSnapshotStateWitnessMetadata,
)
from aware_meta.graph.instance.commit.state_witness import (
    CommitStateWitnessRef,
)


def _clear_fs_store_session_read_cache_for_tests() -> None:
    _runtime_clear_fs_store_session_read_cache_for_tests()


def _snapshot_fs_store_session_read_cache_metrics() -> dict[str, int]:
    return _runtime_snapshot_fs_store_session_read_cache_metrics()


__all__ = [
    "CommitActionDescriptor",
    "CommitEnvelopeReader",
    "CommitStateIndex",
    "CommitStateRow",
    "ClassInstance",
    "FSCommitStore",
    "FSSnapshotStore",
    "JsonObject",
    "LaneCommitBackend",
    "LaneCommitStore",
    "LaneCommitter",
    "LaneHeadCommitReceipt",
    "LaneHeadWatcher",
    "ObjectInstanceGraphCommitBodyRecord",
    "ObjectInstanceGraphCommitEnvelope",
    "ObjectInstanceGraphCommitGraphHashSource",
    "ObjectInstanceGraphCommitHealthMetadata",
    "ObjectInstanceGraphCommitIdentityMetadata",
    "ObjectInstanceGraphCommitIdentitySidecar",
    "ObjectInstanceGraphCommitPreStateEvidence",
    "ObjectInstanceGraphCommitRef",
    "ObjectInstanceGraphCommitRootMetadata",
    "ObjectInstanceGraphSnapshotHealthMetadata",
    "ObjectInstanceGraphSnapshotStateClassSegment",
    "ObjectInstanceGraphSnapshotStateClassSegmentSelection",
    "ObjectInstanceGraphSnapshotStateRawClassSegment",
    "ObjectInstanceGraphSnapshotStateRawClassSegmentIndexSelection",
    "ObjectInstanceGraphSnapshotStateRawClassSegmentSelection",
    "ObjectInstanceGraphSnapshotStateSegmentIndexMetadata",
    "ObjectInstanceGraphSnapshotStateSelection",
    "ObjectInstanceGraphSnapshotStateWitnessMetadata",
    "CommitStateWitnessRef",
    "OigiHistoryDomainCommitProjection",
    "_SESSION_JSON_FILE_CACHE",
    "_clear_fs_store_session_read_cache_for_tests",
    "_commit_state_rows_from_snapshot_payload",
    "_commit_state_rows_read_from_snapshot_payload",
    "_snapshot_fs_store_session_read_cache_metrics",
    "_snapshot_state_rows_payload_hash",
    "_snapshot_state_rows_payload_write",
]
