from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience import ProjectionExperience
    from aware_skill_ontology_dto.skill.skill_config_target import SkillConfigTarget


class SkillConfigExperience(BaseModel):
    # Relationships
    projection_experience: ProjectionExperience | None = Field(default=None)
    targets: list[SkillConfigTarget] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
