from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience_section_graph_binding import (
        ProjectionExperienceSectionGraphBinding,
    )


class ProjectionExperienceLayoutSectionGraphBinding(BaseModel):
    """
    Section graph binding row under ProjectionExperienceLayoutGraphBinding.
    Contract:
    - Groups one existing ProjectionExperienceSectionGraphBinding under one
    layout graph binding.
    - Does not duplicate section, view, graph, or order fields.
    - The parent layout binding validates that the section binding targets a
    section inside the parent Attention LayoutConfig.
    """

    # Relationships
    section_graph_binding: ProjectionExperienceSectionGraphBinding | None = Field(default=None)
