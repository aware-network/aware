from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Skill Ontology Dto
from aware_skill_ontology_dto.skill.skill_run_enums import SkillRunStatus

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_call import ApiCall
    from aware_skill_ontology_dto.skill.skill_config_step import SkillConfigStep


class SkillRunStep(BaseModel):
    # Relationships
    api_call: ApiCall | None = Field(default=None)
    skill_config_step: SkillConfigStep | None = Field(default=None)

    # Attributes
    error: str | None = Field(default=None)
    finished_at_utc: datetime | None = Field(default=None)
    started_at_utc: datetime | None = Field(default=None)
    status: SkillRunStatus = Field(default=SkillRunStatus.queued)
