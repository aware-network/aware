from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.section.section import Section
    from aware_experience_ontology_orm_models.projection.projection_experience_section_view import (
        ProjectionExperienceSectionView,
    )


class ProjectionExperienceSection(ORMModel):
    """
    Experience-owned bridge from ProjectionExperience to an Attention Section.
    Contract:
    - Attention owns Section and FocusScope mutation.
    - Experience owns how one Section resolves to a concrete view instance for
    this ProjectionExperience.
    - Selected Observable matching is derived through the linked view's ApiView.
    - This object does not represent an Environment, Interface, window, layout
    runtime, or focus-scope mount.
    """

    # Relationships
    section: Section | None = Field(default=None)
    section_views: list[ProjectionExperienceSectionView] = Field(default_factory=list)

    # Attributes
    section_key: str | None = Field(
        default=None, description="Optional denormalized lookup text from the Attention Section."
    )

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_sections"
    )
    section_id: UUID = Field(description="Foreign key for ProjectionExperienceSection.section")
