from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_skill_ontology_dto.skill.skill_config_api_endpoint import SkillConfigApiEndpoint
    from aware_skill_ontology_dto.skill.skill_config_step_target import SkillConfigStepTarget


class SkillConfigStep(BaseModel):
    # Relationships
    skill_config_api_endpoint: SkillConfigApiEndpoint
    targets: list[SkillConfigStepTarget] = Field(default_factory=list)

    # Attributes
    instruction: str
    position: int
