from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout_section import LayoutSection
    from aware_experience_ontology_orm_models.projection.projection_experience_view import ProjectionExperienceView


class WindowLayoutSection(ORMModel):
    """Attention Section (observable representation unit) to Experience View (rendering target)"""

    # Relationships
    layout_section: LayoutSection | None = Field(default=None, exclude=True)
    projection_experience_view: ProjectionExperienceView | None = Field(default=None, exclude=True)

    # Foreign Keys
    window_layout_id: UUID = Field(description="Foreign key for WindowLayout.layout_sections")
    layout_section_id: UUID = Field(description="Foreign key for WindowLayoutSection.layout_section")
    projection_experience_view_id: UUID = Field(
        description="Foreign key for WindowLayoutSection.projection_experience_view"
    )
