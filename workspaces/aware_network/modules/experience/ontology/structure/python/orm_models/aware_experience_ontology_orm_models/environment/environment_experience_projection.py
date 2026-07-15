from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience import ProjectionExperience


class EnvironmentExperienceProjection(ORMModel):
    # Relationships
    projection_experience: ProjectionExperience | None = Field(default=None, exclude=True)

    # Foreign Keys
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.experiences"
    )
    projection_experience_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProjection.projection_experience"
    )
