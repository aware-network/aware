from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )


class ProjectionExperienceNodeIdentityEdge(ORMModel):
    """
    Semantic parent->child edge between two ProjectionExperienceNodeIdentity anchors.
    Contract:
    - Topology contract for node identities, independent from runtime class-instance edges.
    - Later materialization can instantiate this into ProjectionExperienceNodeClassIdentityEdge.
    """

    # Relationships
    child_projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(
        default=None, exclude=True
    )
    parent_projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(
        default=None, exclude=True
    )

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_graph_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraph.projection_experience_node_identity_edges"
    )
    child_projection_experience_node_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeIdentityEdge.child_projection_experience_node_identity"
    )
    parent_projection_experience_node_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeIdentityEdge.parent_projection_experience_node_identity"
    )
