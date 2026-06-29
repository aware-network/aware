from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class MetaGraphViewRef(BaseModel):
    """
    Read-only Meta graph view DTOs for renderable graph canvas snapshots.
    Boundary:
    - Requests use Meta-native lane/commit coordinates only.
    - WorkspaceRevision translation belongs above Meta service.
    - Responses expose renderer-safe graph snapshot payloads, not raw runtime
    graph/index objects.
    """

    # Attributes
    graph_kind: str
    id: str | None = Field(default=None)
    stable_identity: str | None = Field(default=None)
    fqn: str | None = Field(default=None)
    namespace: str | None = Field(default=None)
    symbol: str | None = Field(default=None)
    label: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class MetaGraphSnapshotNode(BaseModel):
    # Attributes
    id: str
    label: str
    fqn: str | None = Field(default=None)
    namespace: str | None = Field(default=None)
    symbol: str | None = Field(default=None)
    object_kind: str | None = Field(default=None)
    stable_identity: str | None = Field(default=None)
    position_hint: JsonObject = Field(default_factory=JsonObject)
    metadata: JsonObject = Field(default_factory=JsonObject)


class MetaGraphSnapshotEdge(BaseModel):
    # Attributes
    id: str
    source_node_id: str
    target_node_id: str
    relationship_kind: str | None = Field(default=None)
    label: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class MetaGraphSnapshot(BaseModel):
    # Attributes
    nodes: list[MetaGraphSnapshotNode] = Field(default_factory=list)
    edges: list[MetaGraphSnapshotEdge] = Field(default_factory=list)
    root_identity: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class MetaGraphResolveGraphViewRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    domain_branch_id: UUID
    domain_projection_hash: str
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    projection_name: str | None = Field(default=None)
    view_key: str = Field(default="graph.canvas.v1")
    include_attributes: bool = Field(default=False)
    max_nodes: int | None = Field(default=None)


class MetaGraphResolveGraphViewResponse(BaseModel):
    # Attributes
    status: str
    actor_id: UUID | None = Field(default=None)
    domain_branch_id: UUID
    domain_projection_hash: str
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    object_instance_graph_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    object_config_graph_ref: MetaGraphViewRef | None = Field(default=None)
    object_projection_graph_ref: MetaGraphViewRef | None = Field(default=None)
    object_instance_graph_ref: MetaGraphViewRef | None = Field(default=None)
    object_instance_graph_branch_ref: MetaGraphViewRef | None = Field(default=None)
    object_instance_graph_commit_ref: MetaGraphViewRef | None = Field(default=None)
    graph_snapshot: MetaGraphSnapshot
    summary: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)
    error: str | None = Field(default=None)
