from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Skill Ontology Orm Models
from aware_skill_ontology_orm_models.skill.skill_run_enums import SkillRunStatus

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_call import ApiCall
    from aware_skill_ontology_orm_models.skill.skill_config_step import SkillConfigStep


class SkillRunStep(ORMModel):
    # Relationships
    api_call: ApiCall | None = Field(default=None, exclude=True)
    skill_config_step: SkillConfigStep | None = Field(default=None, exclude=True)

    # Attributes
    error: str | None = Field(default=None)
    finished_at_utc: datetime | None = Field(default=None)
    started_at_utc: datetime | None = Field(default=None)
    status: SkillRunStatus = Field(default=SkillRunStatus.queued)

    # Foreign Keys
    skill_run_id: UUID = Field(description="Foreign key for SkillRun.steps")
    api_call_id: UUID | None = Field(default=None, description="Foreign key for SkillRunStep.api_call")
    skill_config_step_id: UUID = Field(description="Foreign key for SkillRunStep.skill_config_step")
