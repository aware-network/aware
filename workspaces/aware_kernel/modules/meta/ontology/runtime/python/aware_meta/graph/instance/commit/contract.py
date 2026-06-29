from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol, TypeAlias, runtime_checkable
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_history_ontology.lane.lane import Lane
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    CommitStateRow,
)

JsonObject: TypeAlias = dict[str, object]


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphCommitRootMetadata:
    object_instance_graph_key: str
    object_instance_graph_name: str
    object_instance_graph_description: str | None
    root_class_config_id: UUID
    root_source_object_id: UUID


@dataclass(frozen=True, slots=True)
class CommitActionDescriptor:
    """Typed metadata describing the operation that produced a commit."""

    operation_label: str
    call_target: str | None = None
    function_id: UUID | None = None
    object_id: UUID | None = None
    class_instance_identity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphCommitRef:
    branch_id: UUID
    projection_hash: str
    object_instance_graph_commit_id: UUID
    domain_commit_id: UUID
    object_instance_graph_identity_id: UUID | None = None
    object_instance_graph_id: UUID | None = None
    graph_hash_post: str | None = None


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphCommitIdentityMetadata:
    object_instance_graph_id: UUID
    object_instance_graph_identity_id: UUID


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphCommitHealthMetadata:
    commit_id: UUID
    projection_hash: str
    object_instance_graph_id: UUID
    object_instance_graph_identity_id: UUID
    graph_hash_post: str
    parent_count: int
    file_size: int
    file_mtime_ns: int
    file_ctime_ns: int
    file_sha256: str


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphCommitEnvelope:
    commit_id: UUID
    lane_id: UUID
    key: str
    author_id: UUID
    created_at: datetime
    status: str
    parent_commit_ids: tuple[UUID, ...]
    object_instance_graph_commit_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_id: UUID
    object_instance_graph_key: str
    object_instance_graph_name: str
    object_instance_graph_description: str | None
    root_class_config_id: UUID
    root_source_object_id: UUID
    graph_hash_pre: str
    graph_hash_post: str
    projection_hash: str | None
    source_language: str


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphCommitIdentitySidecar:
    commit_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_id: UUID
    parent_commit_ids: tuple[UUID, ...]
    class_instance_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class OigiHistoryDomainCommitProjection:
    domain_commit_id: UUID
    domain_branch_id: UUID
    domain_projection_hash: str
    domain_lane_id: UUID
    history_commit_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_id: UUID
    oigi_projection_hash: str
    oigi_lane_commit_id: UUID
    oigi_graph_hash_post: str


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphSnapshotHealthMetadata:
    commit_id: UUID
    object_instance_graph_id: UUID
    graph_hash: str
    file_size: int
    file_mtime_ns: int
    file_ctime_ns: int
    file_sha256: str


@dataclass(frozen=True, slots=True)
class LaneHeadCommitReceipt:
    """Event emitted after a lane HEAD advances."""

    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    created_at_unix_ms: int
    graph_hash_post: str
    object_instance_graph_id: UUID
    object_instance_graph_commit_id: UUID
    object_instance_graph_identity_id: UUID | None = None
    object_instance_graph_branch_id: UUID | None = None
    object_projection_graph_id: UUID | None = None
    object_projection_graph_identity_id: UUID | None = None
    root_object_id: UUID | None = None
    author_id: UUID | None = None
    commit_action: CommitActionDescriptor | None = None
    class_instance_identity_id: UUID | None = None
    head_version: int = 1


LaneHeadWatcher = Callable[[LaneHeadCommitReceipt], Awaitable[None] | None]


@runtime_checkable
class CommitEnvelopeReader(Protocol):
    def commit_envelope_read_metrics_snapshot(self) -> dict[str, int]: ...

    async def get_commit_envelope(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitEnvelope | None: ...

    async def get_commit_identity_sidecar(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitIdentitySidecar | None: ...


@runtime_checkable
class LaneCommitStore(CommitEnvelopeReader, Protocol):
    @property
    def aware_root(self) -> Path: ...

    def commit_file_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path: ...

    async def get_commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommit | None: ...

    async def head(
        self, *, branch_id: UUID, projection_hash: str
    ) -> JsonObject | None: ...

    async def head_commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> ObjectInstanceGraphCommit | None: ...

    async def head_for_lane(self, *, lane: Lane) -> JsonObject | None: ...

    async def head_commit_for_lane(
        self,
        *,
        lane: Lane,
    ) -> ObjectInstanceGraphCommit | None: ...

    async def iter_lane_heads_by_projection(
        self,
        *,
        projection_hash: str,
    ) -> AsyncIterator[tuple[UUID, JsonObject]]: ...

    async def iter_lineage_forward(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        head_commit_id: UUID,
        stop_at_commit_id: UUID | None,
    ) -> AsyncIterator[ObjectInstanceGraphCommit]: ...


@runtime_checkable
class LaneCommitBackend(LaneCommitStore, Protocol):
    async def put_commit_file(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
        commit_action: CommitActionDescriptor | None = None,
    ) -> bool: ...

    async def append(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
        root_object_id: UUID | None = None,
        commit_action: CommitActionDescriptor | None = None,
        object_projection_graph_identity_id: UUID | None = None,
    ) -> dict[str, int]: ...

    async def domain_commit_id_for_object_instance_graph_commit_id(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_instance_graph_commit_id: UUID,
    ) -> UUID | None: ...

    async def domain_commit_refs_for_object_instance_graph_commit_id(
        self,
        *,
        projection_hash: str,
        object_instance_graph_commit_id: UUID,
    ) -> tuple[ObjectInstanceGraphCommitRef, ...]: ...

    async def domain_commit_refs_for_object_instance_graph_commit_ids(
        self,
        *,
        projection_hash: str,
        object_instance_graph_commit_ids: Iterable[UUID],
        allow_head_fallback: bool = True,
    ) -> dict[UUID, tuple[ObjectInstanceGraphCommitRef, ...]]: ...

    async def get_commit_identity_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitIdentityMetadata | None: ...

    async def get_commit_health_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitHealthMetadata | None: ...

    def write_commit_health_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> None: ...

    async def get_oigi_history_domain_commit_projection(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        domain_commit_id: UUID,
    ) -> OigiHistoryDomainCommitProjection | None: ...

    def put_oigi_history_domain_commit_projection(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        projection: OigiHistoryDomainCommitProjection,
    ) -> bool: ...


@runtime_checkable
class LaneCommitter(Protocol):
    def last_commit_perf_profile_snapshot(self) -> dict[str, int]: ...

    async def commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_projection_graph_identity_id: UUID | None = None,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_id: UUID,
        before_oig: ObjectInstanceGraph,
        root_object_id: UUID | None = None,
        changes: list[ObjectInstanceGraphChange],
        graph_hash_pre: str,
        graph_hash_post: str,
        author_id: UUID,
        commit_id: UUID | None = None,
        source_language: CodeLanguage,
        status: CommitStatus,
        commit_action: CommitActionDescriptor | None = None,
        schema_attribute_configs_by_id: Mapping[UUID, AttributeConfig] | None = None,
    ) -> ObjectInstanceGraphCommit | None: ...

    async def commit_shallow(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_projection_graph_identity_id: UUID | None = None,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_id: UUID,
        pre_state_index: CommitStateIndex,
        root_metadata: ObjectInstanceGraphCommitRootMetadata,
        root_object_id: UUID | None = None,
        changes: list[ObjectInstanceGraphChange],
        graph_hash_pre: str,
        graph_hash_post: str,
        author_id: UUID,
        commit_id: UUID | None = None,
        source_language: CodeLanguage,
        status: CommitStatus,
        commit_action: CommitActionDescriptor | None = None,
    ) -> ObjectInstanceGraphCommit | None: ...


__all__ = [
    "CommitActionDescriptor",
    "CommitEnvelopeReader",
    "CommitStateIndex",
    "CommitStateRow",
    "JsonObject",
    "LaneCommitBackend",
    "LaneCommitStore",
    "LaneCommitter",
    "LaneHeadCommitReceipt",
    "LaneHeadWatcher",
    "ObjectInstanceGraphCommitEnvelope",
    "ObjectInstanceGraphCommitHealthMetadata",
    "ObjectInstanceGraphCommitIdentityMetadata",
    "ObjectInstanceGraphCommitIdentitySidecar",
    "ObjectInstanceGraphCommitRef",
    "ObjectInstanceGraphCommitRootMetadata",
    "ObjectInstanceGraphSnapshotHealthMetadata",
    "OigiHistoryDomainCommitProjection",
]
