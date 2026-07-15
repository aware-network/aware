from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ActorCommit(ORMModel):
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

    # Foreign Keys
    actor_id: UUID = Field(description="Foreign key for Actor.actor_commits")
    object_instance_graph_commit_id: UUID = Field(
        description="Foreign key for ActorCommit.object_instance_graph_commit"
    )

    @classmethod
    async def create_via_actor(
        cls,
        actor_id: UUID,
        domain_branch_id: UUID,
        domain_projection_hash: str,
        domain_commit_id: UUID,
        object_instance_graph_commit_id: UUID,
        environment_id: UUID | None = None,
        process_id: UUID | None = None,
        thread_id: UUID | None = None,
        receipt_actor_id: UUID | None = None,
        created_at_unix_ms: int | None = None,
        operation_label: str | None = None,
        call_target: str | None = None,
        function_id: UUID | None = None,
        object_id: UUID | None = None,
        class_instance_identity_id: UUID | None = None,
        graph_hash_post: str | None = None,
        object_instance_graph_id: UUID | None = None,
        root_object_id: UUID | None = None,
        head_version: int | None = None,
        source: str = "environment_lane_commit_receipt",
    ) -> ActorCommit:
        """
        Create or ensure one ActorCommit personal-history binding.

        This is the post-commit reaction record for Environment lane commit fanout.
        It does not rewrite History Commit authorship; it binds the actor whose
        personal history should include the durable commit.
        """

        payload = {
            "actor_id": actor_id,
            "domain_branch_id": domain_branch_id,
            "domain_projection_hash": domain_projection_hash,
            "domain_commit_id": domain_commit_id,
            "object_instance_graph_commit_id": object_instance_graph_commit_id,
            "environment_id": environment_id,
            "process_id": process_id,
            "thread_id": thread_id,
            "receipt_actor_id": receipt_actor_id,
            "created_at_unix_ms": created_at_unix_ms,
            "operation_label": operation_label,
            "call_target": call_target,
            "function_id": function_id,
            "object_id": object_id,
            "class_instance_identity_id": class_instance_identity_id,
            "graph_hash_post": graph_hash_post,
            "object_instance_graph_id": object_instance_graph_id,
            "root_object_id": root_object_id,
            "head_version": head_version,
            "source": source,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_actor", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActorCommit):
            return value
        return ActorCommit.validate_invocation_value(value)


class ActorCommitCreateViaActorInput(BaseModel):
    actor_id: UUID = Field(description="Foreign key for Actor.actor_commits")
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


class ActorCommitCreateViaActorOutput(BaseModel):
    value: ActorCommit


FUNCTIONS = {
    "ActorCommit": {
        "create_via_actor": {
            "canonical": {
                "name": "create_via_actor",
                "description": "Create or ensure one ActorCommit personal-history binding.\n\nThis is the post-commit reaction record for Environment lane commit fanout.\nIt does not rewrite History Commit authorship; it binds the actor whose\npersonal history should include the durable commit.",
                "is_constructor": True,
            },
            "input": ActorCommitCreateViaActorInput,
            "output": ActorCommitCreateViaActorOutput,
        },
    },
}

__all__ = [
    "ActorCommit",
    "ActorCommitCreateViaActorInput",
    "ActorCommitCreateViaActorOutput",
    "FUNCTIONS",
]
