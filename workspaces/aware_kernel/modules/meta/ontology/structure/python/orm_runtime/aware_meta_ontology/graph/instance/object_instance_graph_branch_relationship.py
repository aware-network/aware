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
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


class ObjectInstanceGraphBranchRelationship(ORMModel):
    # Relationships
    target_object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)

    # Foreign Keys
    object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphBranch.object_instance_graph_branch_relationships"
    )
    target_object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphBranchRelationship.target_object_instance_graph_branch"
    )

    @classmethod
    async def create_via_object_instance_graph_branch(
        cls, object_instance_graph_branch_id: UUID, target_object_instance_graph_branch_id: UUID
    ) -> ObjectInstanceGraphBranchRelationship:
        """
        Creates a Branch→Branch relationship join (idempotent).

        Contract:
        - Source branch identity is parent-propagated when invoked via
          `ObjectInstanceGraphBranch.attach_branch_relationship`.
        - Deterministic id derived from parent source scope + `(target_oigb_id)`.
        - Used by runtime to make portal branch routing commit-backed (no consumer guessing).
        """

        payload = {
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "target_object_instance_graph_branch_id": target_object_instance_graph_branch_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_instance_graph_branch", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectInstanceGraphBranchRelationship):
            return value
        return ObjectInstanceGraphBranchRelationship.validate_invocation_value(value)


class ObjectInstanceGraphBranchRelationshipCreateViaObjectInstanceGraphBranchInput(BaseModel):
    object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphBranch.object_instance_graph_branch_relationships"
    )
    target_object_instance_graph_branch_id: UUID


class ObjectInstanceGraphBranchRelationshipCreateViaObjectInstanceGraphBranchOutput(BaseModel):
    value: ObjectInstanceGraphBranchRelationship


FUNCTIONS = {
    "ObjectInstanceGraphBranchRelationship": {
        "create_via_object_instance_graph_branch": {
            "canonical": {
                "name": "create_via_object_instance_graph_branch",
                "description": "Creates a Branch→Branch relationship join (idempotent).\n\nContract:\n- Source branch identity is parent-propagated when invoked via\n  `ObjectInstanceGraphBranch.attach_branch_relationship`.\n- Deterministic id derived from parent source scope + `(target_oigb_id)`.\n- Used by runtime to make portal branch routing commit-backed (no consumer guessing).",
                "is_constructor": True,
            },
            "input": ObjectInstanceGraphBranchRelationshipCreateViaObjectInstanceGraphBranchInput,
            "output": ObjectInstanceGraphBranchRelationshipCreateViaObjectInstanceGraphBranchOutput,
        },
    },
}

__all__ = [
    "ObjectInstanceGraphBranchRelationship",
    "ObjectInstanceGraphBranchRelationshipCreateViaObjectInstanceGraphBranchInput",
    "ObjectInstanceGraphBranchRelationshipCreateViaObjectInstanceGraphBranchOutput",
    "FUNCTIONS",
]
