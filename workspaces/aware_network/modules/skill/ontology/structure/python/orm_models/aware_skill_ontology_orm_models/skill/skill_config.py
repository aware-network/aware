from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_skill_ontology_orm_models.skill.skill_config_api import SkillConfigApi
    from aware_skill_ontology_orm_models.skill.skill_config_experience import SkillConfigExperience
    from aware_skill_ontology_orm_models.skill.skill_config_step import SkillConfigStep
    from aware_skill_ontology_orm_models.skill.skill_run import SkillRun


class SkillConfig(ORMModel):
    # Relationships
    apis: list[SkillConfigApi] = Field(default_factory=list)
    experiences: list[SkillConfigExperience] = Field(default_factory=list)
    runs: list[SkillRun] = Field(default_factory=list, exclude=True)
    steps: list[SkillConfigStep] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    name: str
