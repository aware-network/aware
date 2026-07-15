from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_graph_identity import (
        ProjectionExperienceGraphIdentity,
    )


class SkillConfigTarget(ORMModel):
    # Relationships
    projection_experience_graph_identity: ProjectionExperienceGraphIdentity | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
    name: str

    # Foreign Keys
    skill_config_experience_id: UUID = Field(description="Foreign key for SkillConfigExperience.targets")
    projection_experience_graph_identity_id: UUID = Field(
        description="Foreign key for SkillConfigTarget.projection_experience_graph_identity"
    )
