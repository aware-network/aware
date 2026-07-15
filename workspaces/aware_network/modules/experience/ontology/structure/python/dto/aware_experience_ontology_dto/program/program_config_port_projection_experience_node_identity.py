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


class ProgramConfigPortProjectionExperienceNodeIdentity(BaseModel):
    """
    Port-level ProjectionExperienceNodeIdentity reference edge.
    Contract:
    - Edge is owned by ProgramConfigPortProjectionExperienceNode.
    - References one stable identity contract owned by ProjectionExperienceNode.
    """

    # Relationships
    projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None)

    # Attributes
    key: str
