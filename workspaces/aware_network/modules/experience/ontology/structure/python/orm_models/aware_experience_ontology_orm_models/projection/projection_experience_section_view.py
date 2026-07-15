from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_view_instance import (
        ProjectionExperienceViewInstance,
    )


class ProjectionExperienceSectionView(ORMModel):
    """
    Section-scoped resolver from a concrete view instance to one Attention section.
    Contract:
    - Attention may select Observable through Section -> FocusScope.
    - Experience resolves Section + selected Observable by deriving Observable
    from the linked view instance's ProjectionExperienceView.api_view.
    - One Observable may have many view configurations globally, but this bridge
    selects the concrete view instance for one ProjectionExperienceSection.
    """

    # Relationships
    projection_experience_view_instance: ProjectionExperienceViewInstance | None = Field(default=None)

    # Attributes
    status: str = Field(default="active")

    # Foreign Keys
    projection_experience_section_id: UUID = Field(
        description="Foreign key for ProjectionExperienceSection.section_views"
    )
    projection_experience_view_instance_id: UUID = Field(
        description="Foreign key for ProjectionExperienceSectionView.projection_experience_view_instance"
    )
