from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.projection.object_projection_graph import ObjectProjectionGraph


class ThreadConfigObjectProjectionGraph(BaseModel):
    """
    Environment ThreadConfig -> Meta ObjectProjectionGraph authority edge.
    Contract:
    - Declares which projection graphs a thread config can host.
    - Does not identify an Experience or view implementation.
    """

    # Relationships
    object_projection_graph: ObjectProjectionGraph | None = Field(default=None)

    # Attributes
    narrative: str | None = Field(
        default=None, description="Narrative text for why this projection graph is part of the thread context."
    )
    intent: str | None = Field(default=None, description="Short canonical intent for this projection graph landing.")
    view_key: str | None = Field(
        default=None, description="Optional canonical view key under the target projection identity."
    )
    position: int | None = Field(default=None, description="Ordering hint for projection clusters.")
    is_default: bool = Field(
        default=False, description="Marks preferred/default projection graph for this thread config."
    )
