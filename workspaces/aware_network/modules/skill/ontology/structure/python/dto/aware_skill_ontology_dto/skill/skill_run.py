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
    from aware_skill_ontology_dto.skill.skill_run_step import SkillRunStep


class SkillRun(BaseModel):
    # Relationships
    steps: list[SkillRunStep] = Field(default_factory=list)

    # Attributes
    error: str | None = Field(default=None)
    finished_at_utc: datetime | None = Field(default=None)
    run_key: str
    started_at_utc: datetime | None = Field(default=None)
    status: SkillRunStatus = Field(default=SkillRunStatus.queued)
