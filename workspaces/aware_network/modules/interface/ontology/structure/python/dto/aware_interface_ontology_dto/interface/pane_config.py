from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience_view import ProjectionExperienceView


class PaneConfig(BaseModel):
    # Relationships
    projection_experience_view: ProjectionExperienceView | None = Field(default=None)

    # Attributes
    name: str
    pane_kind: str
    view_ref: str | None = Field(default=None)
    description: str | None = Field(default=None)
