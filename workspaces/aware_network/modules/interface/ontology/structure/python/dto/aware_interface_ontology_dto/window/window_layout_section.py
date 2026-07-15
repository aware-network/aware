from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.layout.layout_section import LayoutSection
    from aware_experience_ontology_dto.projection.projection_experience_view import ProjectionExperienceView


class WindowLayoutSection(BaseModel):
    """Attention Section (observable representation unit) to Experience View (rendering target)"""

    # Relationships
    layout_section: LayoutSection | None = Field(default=None)
    projection_experience_view: ProjectionExperienceView | None = Field(default=None)
