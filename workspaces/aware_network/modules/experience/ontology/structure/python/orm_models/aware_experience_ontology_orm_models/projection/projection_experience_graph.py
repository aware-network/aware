from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_graph_identity import (
        ProjectionExperienceGraphIdentity,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_graph_identity_edge import (
        ProjectionExperienceGraphIdentityEdge,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_node_identity_edge import (
        ProjectionExperienceNodeIdentityEdge,
    )


class ProjectionExperienceGraph(ORMModel):
    """
    ProjectionExperience graph topology contract.
    Contract:
    - Owns deterministic topology composition over ProjectionExperienceNodeIdentity.
    - API/profile/value bindings are intentionally out of scope.
    """

    # Relationships
    projection_experience_graph_identities: list[ProjectionExperienceGraphIdentity] = Field(
        default_factory=list, exclude=True
    )
    projection_experience_graph_identity_edges: list[ProjectionExperienceGraphIdentityEdge] = Field(
        default_factory=list, exclude=True
    )
    projection_experience_node_identity_edges: list[ProjectionExperienceNodeIdentityEdge] = Field(
        default_factory=list, exclude=True
    )

    # Attributes
    name: str

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_graphs"
    )
