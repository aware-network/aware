from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_history_ontology.commit.commit import Commit
    from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
    from aware_meta_ontology.graph.instance.object_instance_graph_change import ObjectInstanceGraphChange


class ObjectInstanceGraphCommit(ORMModel):
    # Relationships
    object_instance_graph: ObjectInstanceGraph | None = Field(default=None, exclude=True)
    commit: Commit
    object_instance_graph_changes: list[ObjectInstanceGraphChange] = Field(default_factory=list)

    # Attributes
    object_instance_graph_key: str
    object_instance_graph_name: str
    object_instance_graph_description: str | None = Field(default=None)
    root_class_config_id: UUID
    root_source_object_id: UUID
    graph_hash_post: str
    graph_hash_pre: str
    projection_hash: str | None = Field(default=None)
    source_language: CodeLanguage

    # Foreign Keys
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.object_instance_graph_commits"
    )
    object_instance_graph_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphCommit.object_instance_graph"
    )
    commit_id: UUID | None = Field(default=None, description="Foreign key for ObjectInstanceGraphCommit.commit")

    @classmethod
    async def create_via_object_instance_graph_identity(
        cls,
        object_instance_graph_identity_id: UUID,
        commit_id: UUID,
        domain_branch_id: UUID,
        domain_projection_hash: str,
    ) -> ObjectInstanceGraphCommit:
        """
        Materialize a history-plane OIG commit wrapper for a domain commit.

        Canonical v0:
        - Reads the domain commit payload from the commit store (SSOT).
        - Creates (or reuses) the underlying history Commit + CommitParent objects.
        - Parent ObjectInstanceGraphIdentity path context is propagated by traversal lowering.
        - Deterministic identity is constructor-keyed on `(commit_id)` plus parent path.
        - Domain commit payload must carry rooted OIG bootstrap metadata so materialization
          never synthesizes an empty ObjectInstanceGraph.
        """

        payload = {
            "object_instance_graph_identity_id": object_instance_graph_identity_id,
            "commit_id": commit_id,
            "domain_branch_id": domain_branch_id,
            "domain_projection_hash": domain_projection_hash,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_instance_graph_identity", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectInstanceGraphCommit):
            return value
        return ObjectInstanceGraphCommit.validate_invocation_value(value)


class ObjectInstanceGraphCommitCreateViaObjectInstanceGraphIdentityInput(BaseModel):
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.object_instance_graph_commits"
    )
    commit_id: UUID
    domain_branch_id: UUID
    domain_projection_hash: str


class ObjectInstanceGraphCommitCreateViaObjectInstanceGraphIdentityOutput(BaseModel):
    value: ObjectInstanceGraphCommit


FUNCTIONS = {
    "ObjectInstanceGraphCommit": {
        "create_via_object_instance_graph_identity": {
            "canonical": {
                "name": "create_via_object_instance_graph_identity",
                "description": "Materialize a history-plane OIG commit wrapper for a domain commit.\n\nCanonical v0:\n- Reads the domain commit payload from the commit store (SSOT).\n- Creates (or reuses) the underlying history Commit + CommitParent objects.\n- Parent ObjectInstanceGraphIdentity path context is propagated by traversal lowering.\n- Deterministic identity is constructor-keyed on `(commit_id)` plus parent path.\n- Domain commit payload must carry rooted OIG bootstrap metadata so materialization\n  never synthesizes an empty ObjectInstanceGraph.",
                "is_constructor": True,
            },
            "input": ObjectInstanceGraphCommitCreateViaObjectInstanceGraphIdentityInput,
            "output": ObjectInstanceGraphCommitCreateViaObjectInstanceGraphIdentityOutput,
        },
    },
}

__all__ = [
    "ObjectInstanceGraphCommit",
    "ObjectInstanceGraphCommitCreateViaObjectInstanceGraphIdentityInput",
    "ObjectInstanceGraphCommitCreateViaObjectInstanceGraphIdentityOutput",
    "FUNCTIONS",
]
