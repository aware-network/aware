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
    from aware_skill_ontology_orm_models.skill.skill_run_step import SkillRunStep


class SkillRun(ORMModel):
    # Relationships
    steps: list[SkillRunStep] = Field(default_factory=list)

    # Attributes
    error: str | None = Field(default=None)
    finished_at_utc: datetime | None = Field(default=None)
    run_key: str
    started_at_utc: datetime | None = Field(default=None)
    status: SkillRunStatus = Field(default=SkillRunStatus.queued)

    # Foreign Keys
    skill_config_id: UUID = Field(description="Foreign key for SkillConfig.runs")
