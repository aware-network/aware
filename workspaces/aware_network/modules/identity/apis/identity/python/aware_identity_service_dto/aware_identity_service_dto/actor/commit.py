from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class ActorCommitRecord(BaseModel):
    """
    Canonical DTOs for Identity-owned actor commit personal history.
    Contract:
    - `ensure_actor_commit` is the service-facing reaction for Environment lane commit fanout.
    - `resolve_actor_commits` reads the actor-owned personal-history projection.
    - Meta remains the durable commit authority; API records expose only stable provenance fields.
    """

    # Attributes
    actor_commit_id: UUID
    actor_id: UUID
    domain_branch_id: UUID
    domain_projection_hash: str
    domain_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_instance_graph_identity_id: UUID | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    receipt_actor_id: UUID | None = Field(default=None)
    created_at_unix_ms: int | None = Field(default=None)
    operation_label: str | None = Field(default=None)
    call_target: str | None = Field(default=None)
    function_id: UUID | None = Field(default=None)
    object_id: UUID | None = Field(default=None)
    class_instance_identity_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    head_version: int | None = Field(default=None)
    source: str = Field(default="environment_lane_commit_receipt")


class ActorCommitEnsureRequest(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    actor_id: UUID
    domain_branch_id: UUID
    domain_projection_hash: str
    domain_commit_id: UUID
    object_instance_graph_commit_id: UUID
    environment_id: UUID | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    receipt_actor_id: UUID | None = Field(default=None)
    created_at_unix_ms: int | None = Field(default=None)
    operation_label: str | None = Field(default=None)
    call_target: str | None = Field(default=None)
    function_id: UUID | None = Field(default=None)
    object_id: UUID | None = Field(default=None)
    class_instance_identity_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    head_version: int | None = Field(default=None)
    source: str = Field(default="environment_lane_commit_receipt")


class ActorCommitEnsureReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    actor_commit: ActorCommitRecord
    actor_commit_created: bool = Field(default=False)
    info: str | None = Field(default=None)


class ActorCommitResolveRequest(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    actor_id: UUID
    domain_branch_id: UUID | None = Field(default=None)
    domain_projection_hash: str | None = Field(default=None)
    domain_commit_id: UUID | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    receipt_actor_id: UUID | None = Field(default=None)
    function_id: UUID | None = Field(default=None)
    object_id: UUID | None = Field(default=None)
    class_instance_identity_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    source: str | None = Field(default=None)
    limit: int = Field(default=100)


class ActorCommitResolveResult(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    actor_commits: list[ActorCommitRecord] = Field(default_factory=list)
    info: str | None = Field(default=None)
