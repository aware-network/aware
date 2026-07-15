from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience_graph_identity import (
        ProjectionExperienceGraphIdentity,
    )
    from aware_experience_ontology_dto.projection.projection_experience_node_identity_edge import (
        ProjectionExperienceNodeIdentityEdge,
    )


class ProjectionExperienceGraphIdentityEdge(BaseModel):
    """
    Graph occurrence parent->child edge under ProjectionExperienceGraph.
    Contract:
    - Encodes graph occurrence traversal using parent/child ProjectionExperienceGraphIdentity.
    - Requires a semantic ProjectionExperienceNodeIdentityEdge contract boundary.
    """

    # Relationships
    child_projection_experience_graph_identity: ProjectionExperienceGraphIdentity | None = Field(default=None)
    parent_projection_experience_graph_identity: ProjectionExperienceGraphIdentity | None = Field(default=None)
    projection_experience_node_identity_edge: ProjectionExperienceNodeIdentityEdge | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)
