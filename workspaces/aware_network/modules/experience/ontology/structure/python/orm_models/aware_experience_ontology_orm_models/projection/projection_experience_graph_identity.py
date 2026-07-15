from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_graph_identity_profile import (
        ProjectionExperienceGraphIdentityProfile,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )


class ProjectionExperienceGraphIdentity(ORMModel):
    """
    Graph occurrence identity under ProjectionExperienceGraph.
    Contract:
    - Binds one graph occurrence handle to one ProjectionExperienceNodeIdentity.
    - `is_root` marks the canonical root occurrence for deterministic path derivation.
    """

    # Relationships
    projection_experience_graph_identity_profile: ProjectionExperienceGraphIdentityProfile | None = Field(
        default=None, exclude=True
    )
    projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None, exclude=True)

    # Attributes
    is_root: bool = Field(default=False)
    key: str

    # Foreign Keys
    projection_experience_graph_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraph.projection_experience_graph_identities"
    )
    projection_experience_node_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraphIdentity.projection_experience_node_identity"
    )
