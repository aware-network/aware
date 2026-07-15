from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class ProjectionExperienceNodeIdentity(ORMModel):
    """
    ProjectionExperience node identity contract.
    Contract:
    - Declares one human-stable identity name under a ProjectionExperienceNode.
    - Parent->child identity traversal is declared via ProjectionExperienceNodeIdentityEdge.
    """

    # Attributes
    key: str

    # Foreign Keys
    projection_experience_node_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNode.projection_experience_node_identities"
    )
