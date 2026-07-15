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


class MemoryWorkingToolFrame(ORMModel):
    """
    Tool payload for a MemoryWorkingItem.
    Contract:
    - Must be linked to a `MemoryWorkingItem` whose `kind=tool`.
    - Captures canonical action evidence and lane attribution.
    """

    # Relationships
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)

    # Attributes
    tool_call_id: UUID
    tool_response_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)

    # Foreign Keys
    memory_working_item_id: UUID | None = Field(
        default=None, description="Foreign key for MemoryWorkingItem.tool_frame"
    )
    object_instance_graph_branch_id: UUID | None = Field(
        default=None, description="Foreign key for MemoryWorkingToolFrame.object_instance_graph_branch"
    )

    @classmethod
    async def build_via_memory_working_item(
        cls,
        memory_working_item_id: UUID,
        tool_call_id: UUID,
        tool_response_id: UUID | None = None,
        object_instance_graph_branch_id: UUID | None = None,
        projection_hash: str | None = None,
    ) -> MemoryWorkingToolFrame:
        """Builds deterministic tool frame payload for a memory item."""

        payload = {
            "memory_working_item_id": memory_working_item_id,
            "tool_call_id": tool_call_id,
            "tool_response_id": tool_response_id,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "projection_hash": projection_hash,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_memory_working_item", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, MemoryWorkingToolFrame):
            return value
        return MemoryWorkingToolFrame.validate_invocation_value(value)


class MemoryWorkingToolFrameBuildViaMemoryWorkingItemInput(BaseModel):
    memory_working_item_id: UUID = Field(description="Foreign key for MemoryWorkingItem.tool_frame")
    tool_call_id: UUID
    tool_response_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)


class MemoryWorkingToolFrameBuildViaMemoryWorkingItemOutput(BaseModel):
    value: MemoryWorkingToolFrame


FUNCTIONS = {
    "MemoryWorkingToolFrame": {
        "build_via_memory_working_item": {
            "canonical": {
                "name": "build_via_memory_working_item",
                "description": "Builds deterministic tool frame payload for a memory item.",
                "is_constructor": True,
            },
            "input": MemoryWorkingToolFrameBuildViaMemoryWorkingItemInput,
            "output": MemoryWorkingToolFrameBuildViaMemoryWorkingItemOutput,
        },
    },
}

__all__ = [
    "MemoryWorkingToolFrame",
    "MemoryWorkingToolFrameBuildViaMemoryWorkingItemInput",
    "MemoryWorkingToolFrameBuildViaMemoryWorkingItemOutput",
    "FUNCTIONS",
]
