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


class ServiceConfigExperience(ORMModel):
    # Relationships
    projection_experience: ProjectionExperience | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.experiences")
    projection_experience_id: UUID = Field(description="Foreign key for ServiceConfigExperience.projection_experience")
