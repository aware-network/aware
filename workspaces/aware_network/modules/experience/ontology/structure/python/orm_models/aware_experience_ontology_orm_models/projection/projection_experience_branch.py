from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class ProjectionExperienceBranch(ORMModel):
    # Attributes
    name: str

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_branches"
    )
