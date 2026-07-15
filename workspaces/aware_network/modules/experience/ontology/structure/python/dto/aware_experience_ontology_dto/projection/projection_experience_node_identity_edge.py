from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )


class ProjectionExperienceNodeIdentityEdge(BaseModel):
    """
    Semantic parent->child edge between two ProjectionExperienceNodeIdentity anchors.
    Contract:
    - Topology contract for node identities, independent from runtime class-instance edges.
    - Later materialization can instantiate this into ProjectionExperienceNodeClassIdentityEdge.
    """

    # Relationships
    child_projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None)
    parent_projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)
