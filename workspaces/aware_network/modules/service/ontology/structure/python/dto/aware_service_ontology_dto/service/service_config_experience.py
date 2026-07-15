from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience import ProjectionExperience


class ServiceConfigExperience(BaseModel):
    # Relationships
    projection_experience: ProjectionExperience | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
