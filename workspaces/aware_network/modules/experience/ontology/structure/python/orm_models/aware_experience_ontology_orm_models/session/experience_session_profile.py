from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.environment.environment_experience_profile import (
        EnvironmentExperienceProfile,
    )


class ExperienceSessionProfile(ORMModel):
    """
    Session-local mount of one applied Experience profile.
    Contract:
    - EnvironmentExperienceProfile remains reusable applied profile truth.
    - This row records participation/provenance within one ExperienceSession.
    - It carries no global active-profile or active-projection semantics.
    """

    # Relationships
    profile: EnvironmentExperienceProfile | None = Field(default=None)

    # Attributes
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    experience_session_id: UUID = Field(description="Foreign key for ExperienceSession.profiles")
    profile_id: UUID = Field(description="Foreign key for ExperienceSessionProfile.profile")
