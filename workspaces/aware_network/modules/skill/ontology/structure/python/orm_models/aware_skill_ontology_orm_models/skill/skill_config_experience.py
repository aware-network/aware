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
    from aware_skill_ontology_orm_models.skill.skill_config_target import SkillConfigTarget


class SkillConfigExperience(ORMModel):
    # Relationships
    projection_experience: ProjectionExperience | None = Field(default=None)
    targets: list[SkillConfigTarget] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    skill_config_id: UUID = Field(description="Foreign key for SkillConfig.experiences")
    projection_experience_id: UUID = Field(description="Foreign key for SkillConfigExperience.projection_experience")
