from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config_port_projection_experience_node_identity import (
        ProgramConfigPortProjectionExperienceNodeIdentity,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_node import ProjectionExperienceNode


class ProgramConfigPortProjectionExperienceNode(ORMModel):
    """
    Port-level ProjectionExperienceNode reference edge.
    Contract:
    - Port does not declare structural traversal; it references one ProjectionExperienceNode
    owned by ProjectionExperience contracts.
    - Node-level identities are attached under this edge.
    """

    # Relationships
    projection_experience_node: ProjectionExperienceNode | None = Field(default=None, exclude=True)
    projection_node_identity: ProgramConfigPortProjectionExperienceNodeIdentity | None = Field(
        default=None, exclude=True
    )

    # Attributes
    key: str

    # Foreign Keys
    program_config_port_id: UUID = Field(description="Foreign key for ProgramConfigPort.projection_nodes")
    projection_experience_node_id: UUID = Field(
        description="Foreign key for ProgramConfigPortProjectionExperienceNode.projection_experience_node"
    )
