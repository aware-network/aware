from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_node_key import ObjectProjectionGraphNodeKey


class ProjectionExperienceNodeKey(BaseModel):
    """
    ProjectionExperience node key compatibility wrapper.
    Contract:
    - Declares one deterministic ProjectionKey consumer row under ProjectionExperienceNode.
    - Canonical key schema is owned by Meta `ObjectProjectionGraphNodeKey`.
    """

    # Relationships
    object_projection_graph_node_key: ObjectProjectionGraphNodeKey | None = Field(default=None)
