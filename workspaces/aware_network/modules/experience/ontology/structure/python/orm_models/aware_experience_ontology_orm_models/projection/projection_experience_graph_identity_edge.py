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
    from aware_experience_ontology_orm_models.projection.projection_experience_node_identity_edge import (
        ProjectionExperienceNodeIdentityEdge,
    )


class ProjectionExperienceGraphIdentityEdge(ORMModel):
    """
    Graph occurrence parent->child edge under ProjectionExperienceGraph.
    Contract:
    - Encodes graph occurrence traversal using parent/child ProjectionExperienceGraphIdentity.
    - Requires a semantic ProjectionExperienceNodeIdentityEdge contract boundary.
    """

    # Relationships
    child_projection_experience_graph_identity: ProjectionExperienceGraphIdentity | None = Field(
        default=None, exclude=True
    )
    parent_projection_experience_graph_identity: ProjectionExperienceGraphIdentity | None = Field(
        default=None, exclude=True
    )
    projection_experience_node_identity_edge: ProjectionExperienceNodeIdentityEdge | None = Field(
        default=None, exclude=True
    )

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_graph_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraph.projection_experience_graph_identity_edges"
    )
    child_projection_experience_graph_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraphIdentityEdge.child_projection_experience_graph_identity"
    )
    parent_projection_experience_graph_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraphIdentityEdge.parent_projection_experience_graph_identity"
    )
    projection_experience_node_identity_edge_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraphIdentityEdge.projection_experience_node_identity_edge"
    )
