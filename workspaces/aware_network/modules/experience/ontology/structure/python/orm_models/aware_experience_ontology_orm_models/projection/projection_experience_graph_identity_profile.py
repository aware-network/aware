from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_graph_identity_profile_exemplar import (
        ProjectionExperienceGraphIdentityProfileExemplar,
    )


class ProjectionExperienceGraphIdentityProfile(ORMModel):
    """
    Canonical profile for one ProjectionExperienceGraphIdentity.
    Contract:
    - Owned by one graph occurrence identity, not by generic node identity.
    - Stores review-facing label and deterministic resolution hints for later
    profile-based binding.
    - Remains perception-agnostic: it holds identity-side truth, not observations.
    """

    # Relationships
    exemplars: list[ProjectionExperienceGraphIdentityProfileExemplar] = Field(default_factory=list, exclude=True)

    # Attributes
    review_label: str
    resolution_prompts: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    summary: str | None = Field(default=None)
    notes: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_graph_identity_id: UUID | None = Field(
        default=None,
        description="Foreign key for ProjectionExperienceGraphIdentity.projection_experience_graph_identity_profile",
    )
