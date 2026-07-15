from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience_graph_identity_profile_exemplar import (
        ProjectionExperienceGraphIdentityProfileExemplar,
    )


class ProjectionExperienceGraphIdentityProfile(BaseModel):
    """
    Canonical profile for one ProjectionExperienceGraphIdentity.
    Contract:
    - Owned by one graph occurrence identity, not by generic node identity.
    - Stores review-facing label and deterministic resolution hints for later
    profile-based binding.
    - Remains perception-agnostic: it holds identity-side truth, not observations.
    """

    # Relationships
    exemplars: list[ProjectionExperienceGraphIdentityProfileExemplar] = Field(default_factory=list)

    # Attributes
    review_label: str
    resolution_prompts: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    summary: str | None = Field(default=None)
    notes: str | None = Field(default=None)
