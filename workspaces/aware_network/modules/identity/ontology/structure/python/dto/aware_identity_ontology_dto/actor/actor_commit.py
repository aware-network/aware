from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ActorCommit(BaseModel):
    """
    Identity-owned personal-history binding from Actor to a durable lane commit.
    Contract:
    - Actor owns the personal-history row.
    - Meta remains the commit authority through ObjectInstanceGraphCommit.
    - The idempotency coordinate is `(actor_id, domain_branch_id, domain_projection_hash, domain_commit_id)`.
    - `object_instance_graph_commit` is mandatory provenance for every ActorCommit.
    """

    # Relationships
    object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    domain_branch_id: UUID
    domain_projection_hash: str
    domain_commit_id: UUID
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
