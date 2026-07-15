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


class ProgramConfigPortProjectionExperienceNodeIdentity(ORMModel):
    """
    Port-level ProjectionExperienceNodeIdentity reference edge.
    Contract:
    - Edge is owned by ProgramConfigPortProjectionExperienceNode.
    - References one stable identity contract owned by ProjectionExperienceNode.
    """

    # Relationships
    projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None, exclude=True)

    # Attributes
    key: str

    # Foreign Keys
    program_config_port_projection_experience_node_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramConfigPortProjectionExperienceNode.projection_node_identity"
    )
    projection_experience_node_identity_id: UUID = Field(
        description="Foreign key for ProgramConfigPortProjectionExperienceNodeIdentity.projection_experience_node_identity"
    )
