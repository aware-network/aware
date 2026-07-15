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
    from aware_experience_ontology_dto.projection.projection_experience_layout_graph_binding import (
        ProjectionExperienceLayoutGraphBinding,
    )


class AppConfigScreenConfig(BaseModel):
    # Relationships
    projection_experience: ProjectionExperience | None = Field(default=None)
    projection_experience_layout_graph_binding: ProjectionExperienceLayoutGraphBinding | None = Field(default=None)

    # Attributes
    screen_key: str
