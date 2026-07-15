from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience_node_key import ProjectionExperienceNodeKey


class ProjectionExperienceNodeClassIdentityKeyBinding(BaseModel):
    """
    ProjectionKey payload row under ProjectionExperienceNodeClassIdentity.
    Contract:
    - Binds one consumed ProjectionExperienceNodeKey to one concrete payload used for resolution proof.
    """

    # Relationships
    projection_experience_node_key: ProjectionExperienceNodeKey | None = Field(default=None)

    # Attributes
    value: JsonObject | None = Field(default=None)
