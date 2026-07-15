from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_config_port_projection_experience_node_identity import (
        ProgramConfigPortProjectionExperienceNodeIdentity,
    )
    from aware_experience_ontology_dto.projection.projection_experience_node import ProjectionExperienceNode


class ProgramConfigPortProjectionExperienceNode(BaseModel):
    """
    Port-level ProjectionExperienceNode reference edge.
    Contract:
    - Port does not declare structural traversal; it references one ProjectionExperienceNode
    owned by ProjectionExperience contracts.
    - Node-level identities are attached under this edge.
    """

    # Relationships
    projection_experience_node: ProjectionExperienceNode | None = Field(default=None)
    projection_node_identity: ProgramConfigPortProjectionExperienceNodeIdentity | None = Field(default=None)

    # Attributes
    key: str
