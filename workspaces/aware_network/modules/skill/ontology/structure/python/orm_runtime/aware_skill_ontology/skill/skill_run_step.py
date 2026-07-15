from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Skill Ontology
from aware_skill_ontology.skill.skill_run_enums import SkillRunStatus

if TYPE_CHECKING:
    from aware_api_ontology.api.api_call import ApiCall
    from aware_skill_ontology.skill.skill_config_step import SkillConfigStep


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

    @classmethod
    async def build_via_skill_run(
        cls,
        skill_run_id: UUID,
        skill_config_step_id: UUID,
        api_call_id: UUID | None = None,
        status: SkillRunStatus = SkillRunStatus.queued,
        started_at_utc: datetime | None = None,
        finished_at_utc: datetime | None = None,
        error: str | None = None,
    ) -> SkillRunStep:
        """
        Create one Skill-owned step execution receipt.

        Contract:
        - This object reports Skill orchestration state only.
        - The referenced `SkillConfigStep` owns authored instruction and ordering.
        - The referenced `ApiCall`, when present, owns request and response payload truth.
        """

        payload = {
            "skill_run_id": skill_run_id,
            "skill_config_step_id": skill_config_step_id,
            "api_call_id": api_call_id,
            "status": status,
            "started_at_utc": started_at_utc,
            "finished_at_utc": finished_at_utc,
            "error": error,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_skill_run", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SkillRunStep):
            return value
        return SkillRunStep.validate_invocation_value(value)


class SkillRunStepBuildViaSkillRunInput(BaseModel):
    skill_run_id: UUID = Field(description="Foreign key for SkillRun.steps")
    skill_config_step_id: UUID
    api_call_id: UUID | None = Field(default=None)
    status: SkillRunStatus = Field(default=SkillRunStatus.queued)
    started_at_utc: datetime | None = Field(default=None)
    finished_at_utc: datetime | None = Field(default=None)
    error: str | None = Field(default=None)


class SkillRunStepBuildViaSkillRunOutput(BaseModel):
    value: SkillRunStep


FUNCTIONS = {
    "SkillRunStep": {
        "build_via_skill_run": {
            "canonical": {
                "name": "build_via_skill_run",
                "description": "Create one Skill-owned step execution receipt.\n\nContract:\n- This object reports Skill orchestration state only.\n- The referenced `SkillConfigStep` owns authored instruction and ordering.\n- The referenced `ApiCall`, when present, owns request and response payload truth.",
                "is_constructor": True,
            },
            "input": SkillRunStepBuildViaSkillRunInput,
            "output": SkillRunStepBuildViaSkillRunOutput,
        },
    },
}

__all__ = [
    "SkillRunStep",
    "SkillRunStepBuildViaSkillRunInput",
    "SkillRunStepBuildViaSkillRunOutput",
    "FUNCTIONS",
]
