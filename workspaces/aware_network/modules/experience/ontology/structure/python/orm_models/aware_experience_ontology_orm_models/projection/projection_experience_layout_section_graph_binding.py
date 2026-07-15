from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_section_graph_binding import (
        ProjectionExperienceSectionGraphBinding,
    )


class ProjectionExperienceLayoutSectionGraphBinding(ORMModel):
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
    section_graph_binding: ProjectionExperienceSectionGraphBinding | None = Field(default=None, exclude=True)

    # Foreign Keys
    projection_experience_layout_graph_binding_id: UUID = Field(
        description="Foreign key for ProjectionExperienceLayoutGraphBinding.layout_section_graph_bindings"
    )
    section_graph_binding_id: UUID = Field(
        description="Foreign key for ProjectionExperienceLayoutSectionGraphBinding.section_graph_binding"
    )
