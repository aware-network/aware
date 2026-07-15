from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_skill_ontology_orm_models.skill.skill_config_target import SkillConfigTarget


class SkillConfigStepTarget(ORMModel):
    # Relationships
    skill_config_target: SkillConfigTarget

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    skill_config_step_id: UUID = Field(description="Foreign key for SkillConfigStep.targets")
    skill_config_target_id: UUID | None = Field(
        default=None, description="Foreign key for SkillConfigStepTarget.skill_config_target"
    )
