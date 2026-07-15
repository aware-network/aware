from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


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
