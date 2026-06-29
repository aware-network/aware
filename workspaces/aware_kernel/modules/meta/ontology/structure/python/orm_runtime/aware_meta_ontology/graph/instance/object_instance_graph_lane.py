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
    from aware_history_ontology.lane.lane import Lane
    from aware_meta_ontology.function.function_call import FunctionCall


class ObjectInstanceGraphLane(ORMModel):
    # Relationships
    lane: Lane = Field(description="Lane Identity")
    function_calls: list[FunctionCall] = Field(
        default_factory=list, description="Function-call execution history for this lane."
    )

    # Foreign Keys
    object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphBranch.object_instance_graph_lanes"
    )
    lane_id: UUID | None = Field(default=None, description="Foreign key for ObjectInstanceGraphLane.lane")

    async def create_function_call(
        self,
        call_key: UUID,
        function_config_id: UUID,
        target_class_instance_identity_id: UUID | None = None,
        base_commit_id: UUID | None = None,
        graph_hash_pre: str | None = None,
    ) -> FunctionCall:
        """
        Create one durable function-call request envelope under this OIG lane.

        Contract:
        - Parent ObjectInstanceGraphLane path context is propagated by traversal lowering.
        - `call_key` is the per-invocation identity; repeated calls on the same
          lane/function must not collapse.
        - FunctionCall is the Meta-owned execution root. Generic OIGOperation
          wrappers are intentionally not part of the clean rail.
        """

        payload = {
            "call_key": call_key,
            "function_config_id": function_config_id,
            "target_class_instance_identity_id": target_class_instance_identity_id,
            "base_commit_id": base_commit_id,
            "graph_hash_pre": graph_hash_pre,
        }
        result = await invoke_instance(orm_model=self, function_name="create_function_call", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_call import FunctionCall

        if isinstance(value, FunctionCall):
            return value
        return FunctionCall.validate_invocation_value(value)

    @classmethod
    async def create_via_object_instance_graph_branch(
        cls, object_instance_graph_branch_id: UUID, lane_id: UUID
    ) -> ObjectInstanceGraphLane:
        """
        Creates a linkage meta.ObjectInstanceGraphBranch to history.lane.

        Contract:
        - Parent ObjectInstanceGraphBranch path context is propagated by traversal lowering.
        - Deterministic identity is constructor-keyed on `(lane_id)` plus parent path.
        """

        payload = {"object_instance_graph_branch_id": object_instance_graph_branch_id, "lane_id": lane_id}
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_instance_graph_branch", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectInstanceGraphLane):
            return value
        return ObjectInstanceGraphLane.validate_invocation_value(value)


class ObjectInstanceGraphLaneCreateFunctionCallInput(BaseModel):
    call_key: UUID
    function_config_id: UUID
    target_class_instance_identity_id: UUID | None = Field(default=None)
    base_commit_id: UUID | None = Field(default=None)
    graph_hash_pre: str | None = Field(default=None)


class ObjectInstanceGraphLaneCreateFunctionCallOutput(BaseModel):
    value: FunctionCall


class ObjectInstanceGraphLaneCreateViaObjectInstanceGraphBranchInput(BaseModel):
    object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphBranch.object_instance_graph_lanes"
    )
    lane_id: UUID


class ObjectInstanceGraphLaneCreateViaObjectInstanceGraphBranchOutput(BaseModel):
    value: ObjectInstanceGraphLane


FUNCTIONS = {
    "ObjectInstanceGraphLane": {
        "create_function_call": {
            "canonical": {
                "name": "create_function_call",
                "description": "Create one durable function-call request envelope under this OIG lane.\n\nContract:\n- Parent ObjectInstanceGraphLane path context is propagated by traversal lowering.\n- `call_key` is the per-invocation identity; repeated calls on the same\n  lane/function must not collapse.\n- FunctionCall is the Meta-owned execution root. Generic OIGOperation\n  wrappers are intentionally not part of the clean rail.",
                "is_constructor": False,
            },
            "input": ObjectInstanceGraphLaneCreateFunctionCallInput,
            "output": ObjectInstanceGraphLaneCreateFunctionCallOutput,
        },
        "create_via_object_instance_graph_branch": {
            "canonical": {
                "name": "create_via_object_instance_graph_branch",
                "description": "Creates a linkage meta.ObjectInstanceGraphBranch to history.lane.\n\nContract:\n- Parent ObjectInstanceGraphBranch path context is propagated by traversal lowering.\n- Deterministic identity is constructor-keyed on `(lane_id)` plus parent path.",
                "is_constructor": True,
            },
            "input": ObjectInstanceGraphLaneCreateViaObjectInstanceGraphBranchInput,
            "output": ObjectInstanceGraphLaneCreateViaObjectInstanceGraphBranchOutput,
        },
    },
}

__all__ = [
    "ObjectInstanceGraphLane",
    "ObjectInstanceGraphLaneCreateFunctionCallInput",
    "ObjectInstanceGraphLaneCreateFunctionCallOutput",
    "ObjectInstanceGraphLaneCreateViaObjectInstanceGraphBranchInput",
    "ObjectInstanceGraphLaneCreateViaObjectInstanceGraphBranchOutput",
    "FUNCTIONS",
]
