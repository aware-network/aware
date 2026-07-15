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
    from aware_experience_ontology_dto.projection.projection_experience_graph_identity_edge import (
        ProjectionExperienceGraphIdentityEdge,
    )
    from aware_experience_ontology_dto.projection.projection_experience_node_identity_edge import (
        ProjectionExperienceNodeIdentityEdge,
    )


class ProjectionExperienceGraph(BaseModel):
    """
    ProjectionExperience graph topology contract.
    Contract:
    - Owns deterministic topology composition over ProjectionExperienceNodeIdentity.
    - API/profile/value bindings are intentionally out of scope.
    """

    # Relationships
    projection_experience_graph_identities: list[ProjectionExperienceGraphIdentity] = Field(default_factory=list)
    projection_experience_graph_identity_edges: list[ProjectionExperienceGraphIdentityEdge] = Field(
        default_factory=list
    )
    projection_experience_node_identity_edges: list[ProjectionExperienceNodeIdentityEdge] = Field(default_factory=list)

    # Attributes
    name: str
