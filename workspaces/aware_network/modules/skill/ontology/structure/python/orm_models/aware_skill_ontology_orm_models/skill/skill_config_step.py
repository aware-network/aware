from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_skill_ontology_orm_models.skill.skill_config_api_endpoint import SkillConfigApiEndpoint
    from aware_skill_ontology_orm_models.skill.skill_config_step_target import SkillConfigStepTarget


class SkillConfigStep(ORMModel):
    # Relationships
    skill_config_api_endpoint: SkillConfigApiEndpoint
    targets: list[SkillConfigStepTarget] = Field(default_factory=list)

    # Attributes
    instruction: str
    position: int

    # Foreign Keys
    skill_config_id: UUID = Field(description="Foreign key for SkillConfig.steps")
    skill_config_api_endpoint_id: UUID | None = Field(
        default=None, description="Foreign key for SkillConfigStep.skill_config_api_endpoint"
    )
