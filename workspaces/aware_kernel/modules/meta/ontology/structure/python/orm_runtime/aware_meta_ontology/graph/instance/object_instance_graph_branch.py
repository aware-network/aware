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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_history_ontology.branch.branch import Branch
    from aware_meta_ontology.graph.instance.object_instance_graph_branch_relationship import (
        ObjectInstanceGraphBranchRelationship,
    )
    from aware_meta_ontology.graph.instance.object_instance_graph_lane import ObjectInstanceGraphLane


class ObjectInstanceGraphBranch(ORMModel):
    """A Meta pointer to Branch to link Lane->Commit to ObjectInstanceGraphLanes with Meta Representation at ObjectInstanceGraph level."""

    # Relationships
    branch: Branch = Field(description="Branch Identity")
    object_instance_graph_lanes: list[ObjectInstanceGraphLane] = Field(
        default_factory=list, description="Projection Lanes"
    )
    object_instance_graph_branch_relationships: list[ObjectInstanceGraphBranchRelationship] = Field(
        default_factory=list, description="Branch Relationships"
    )

    # Foreign Keys
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.object_instance_graph_branches"
    )
    branch_id: UUID | None = Field(default=None, description="Foreign key for ObjectInstanceGraphBranch.branch")

    async def attach_lane(self, lane_id: UUID) -> ObjectInstanceGraphLane:
        """
        Attaches a history Lane to this ObjectInstanceGraphBranch (idempotent).

        Contract:
        - Mutates the meta association `object_instance_graph_lanes`, so it must be
          invoked as an instance function (runtime mutate-self-only).
        - Creates the ObjectInstanceGraphLane via its own constructor if missing.
        """

        payload = {"lane_id": lane_id}
        result = await invoke_instance(orm_model=self, function_name="attach_lane", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.instance.object_instance_graph_lane import ObjectInstanceGraphLane

        if isinstance(value, ObjectInstanceGraphLane):
            return value
        return ObjectInstanceGraphLane.validate_invocation_value(value)

    async def attach_branch_relationship(
        self, target_object_instance_graph_branch_id: UUID
    ) -> ObjectInstanceGraphBranchRelationship:
        """
        Attaches a Branch→Branch relationship (idempotent).

        Notes:
        - This is a history-plane index primitive used for portal branch routing.
        - Mutates only `object_instance_graph_branch_relationships` (runtime mutate-self-only).
        """

        payload = {"target_object_instance_graph_branch_id": target_object_instance_graph_branch_id}
        result = await invoke_instance(orm_model=self, function_name="attach_branch_relationship", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.instance.object_instance_graph_branch_relationship import (
            ObjectInstanceGraphBranchRelationship,
        )

        if isinstance(value, ObjectInstanceGraphBranchRelationship):
            return value
        return ObjectInstanceGraphBranchRelationship.validate_invocation_value(value)

    @classmethod
    async def create_with_lane_and_branch_via_object_instance_graph_identity(
        cls,
        object_instance_graph_identity_id: UUID,
        branch_id: UUID,
        lane_id: UUID,
        commit_id: UUID,
        lane_hash: str,
        is_main: bool = False,
        name: str | None = None,
    ) -> ObjectInstanceGraphBranch:
        """
        Create deterministic ObjectInstanceGraphBranch with one initial lane + branch head link.

        Contract:
        - Parent ObjectInstanceGraphIdentity path context is propagated by traversal lowering.
        - Deterministic identity is constructor-keyed on `(branch_id)` plus parent path.
        """

        payload = {
            "object_instance_graph_identity_id": object_instance_graph_identity_id,
            "branch_id": branch_id,
            "lane_id": lane_id,
            "commit_id": commit_id,
            "lane_hash": lane_hash,
            "is_main": is_main,
            "name": name,
        }
        result = await invoke_constructor(
            orm_class=cls,
            function_name="create_with_lane_and_branch_via_object_instance_graph_identity",
            payload=payload,
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectInstanceGraphBranch):
            return value
        return ObjectInstanceGraphBranch.validate_invocation_value(value)


class ObjectInstanceGraphBranchAttachLaneInput(BaseModel):
    lane_id: UUID


class ObjectInstanceGraphBranchAttachLaneOutput(BaseModel):
    value: ObjectInstanceGraphLane


class ObjectInstanceGraphBranchAttachBranchRelationshipInput(BaseModel):
    target_object_instance_graph_branch_id: UUID


class ObjectInstanceGraphBranchAttachBranchRelationshipOutput(BaseModel):
    value: ObjectInstanceGraphBranchRelationship


class ObjectInstanceGraphBranchCreateWithLaneAndBranchViaObjectInstanceGraphIdentityInput(BaseModel):
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.object_instance_graph_branches"
    )
    branch_id: UUID
    lane_id: UUID
    commit_id: UUID
    lane_hash: str
    is_main: bool = Field(default=False)
    name: str | None = Field(default=None)


class ObjectInstanceGraphBranchCreateWithLaneAndBranchViaObjectInstanceGraphIdentityOutput(BaseModel):
    value: ObjectInstanceGraphBranch


FUNCTIONS = {
    "ObjectInstanceGraphBranch": {
        "attach_lane": {
            "canonical": {
                "name": "attach_lane",
                "description": "Attaches a history Lane to this ObjectInstanceGraphBranch (idempotent).\n\nContract:\n- Mutates the meta association `object_instance_graph_lanes`, so it must be\n  invoked as an instance function (runtime mutate-self-only).\n- Creates the ObjectInstanceGraphLane via its own constructor if missing.",
                "is_constructor": False,
            },
            "input": ObjectInstanceGraphBranchAttachLaneInput,
            "output": ObjectInstanceGraphBranchAttachLaneOutput,
        },
        "attach_branch_relationship": {
            "canonical": {
                "name": "attach_branch_relationship",
                "description": "Attaches a Branch→Branch relationship (idempotent).\n\nNotes:\n- This is a history-plane index primitive used for portal branch routing.\n- Mutates only `object_instance_graph_branch_relationships` (runtime mutate-self-only).",
                "is_constructor": False,
            },
            "input": ObjectInstanceGraphBranchAttachBranchRelationshipInput,
            "output": ObjectInstanceGraphBranchAttachBranchRelationshipOutput,
        },
        "create_with_lane_and_branch_via_object_instance_graph_identity": {
            "canonical": {
                "name": "create_with_lane_and_branch_via_object_instance_graph_identity",
                "description": "Create deterministic ObjectInstanceGraphBranch with one initial lane + branch head link.\n\nContract:\n- Parent ObjectInstanceGraphIdentity path context is propagated by traversal lowering.\n- Deterministic identity is constructor-keyed on `(branch_id)` plus parent path.",
                "is_constructor": True,
            },
            "input": ObjectInstanceGraphBranchCreateWithLaneAndBranchViaObjectInstanceGraphIdentityInput,
            "output": ObjectInstanceGraphBranchCreateWithLaneAndBranchViaObjectInstanceGraphIdentityOutput,
        },
    },
}

__all__ = [
    "ObjectInstanceGraphBranch",
    "ObjectInstanceGraphBranchAttachLaneInput",
    "ObjectInstanceGraphBranchAttachLaneOutput",
    "ObjectInstanceGraphBranchAttachBranchRelationshipInput",
    "ObjectInstanceGraphBranchAttachBranchRelationshipOutput",
    "ObjectInstanceGraphBranchCreateWithLaneAndBranchViaObjectInstanceGraphIdentityInput",
    "ObjectInstanceGraphBranchCreateWithLaneAndBranchViaObjectInstanceGraphIdentityOutput",
    "FUNCTIONS",
]
