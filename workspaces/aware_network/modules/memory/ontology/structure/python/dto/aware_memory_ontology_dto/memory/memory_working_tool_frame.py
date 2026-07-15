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
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


class MemoryWorkingToolFrame(BaseModel):
    """
    Tool payload for a MemoryWorkingItem.
    Contract:
    - Must be linked to a `MemoryWorkingItem` whose `kind=tool`.
    - Captures canonical action evidence and lane attribution.
    """

    # Relationships
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)

    # Attributes
    tool_call_id: UUID
    tool_response_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
