from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.section.section import Section
    from aware_experience_ontology_dto.projection.projection_experience_section_view import (
        ProjectionExperienceSectionView,
    )


class ProjectionExperienceSection(BaseModel):
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
