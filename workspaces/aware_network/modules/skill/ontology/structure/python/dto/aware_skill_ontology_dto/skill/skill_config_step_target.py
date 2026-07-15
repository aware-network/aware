from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_skill_ontology_dto.skill.skill_config_target import SkillConfigTarget


class SkillConfigStepTarget(BaseModel):
    # Relationships
    skill_config_target: SkillConfigTarget

    # Attributes
    description: str | None = Field(default=None)
