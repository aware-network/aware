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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Skill Ontology
from aware_skill_ontology.skill.skill_run_enums import SkillRunStatus

if TYPE_CHECKING:
    from aware_skill_ontology.skill.skill_run_step import SkillRunStep


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

    async def create_step(
        self,
        skill_config_step_id: UUID,
        api_call_id: UUID | None = None,
        status: SkillRunStatus = SkillRunStatus.queued,
        started_at_utc: datetime | None = None,
        finished_at_utc: datetime | None = None,
        error: str | None = None,
    ) -> SkillRunStep:
        """
        Attach one execution receipt for an authored SkillConfigStep.

        Contract:
        - `skill_config_step_id` is the authored step identity and supplies ordering.
        - `api_call_id` is optional while queued/running/skipped, but terminal invoked steps
          must attach API-owned call truth at the service/runtime layer.
        """

        payload = {
            "skill_config_step_id": skill_config_step_id,
            "api_call_id": api_call_id,
            "status": status,
            "started_at_utc": started_at_utc,
            "finished_at_utc": finished_at_utc,
            "error": error,
        }
        result = await invoke_instance(orm_model=self, function_name="create_step", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_skill_ontology.skill.skill_run_step import SkillRunStep

        if isinstance(value, SkillRunStep):
            return value
        return SkillRunStep.validate_invocation_value(value)

    @classmethod
    async def build_via_skill_config(
        cls,
        skill_config_id: UUID,
        run_key: str,
        status: SkillRunStatus = SkillRunStatus.queued,
        started_at_utc: datetime | None = None,
        finished_at_utc: datetime | None = None,
        error: str | None = None,
    ) -> SkillRun:
        """
        Create one Skill-owned orchestration run receipt.

        Contract:
        - `SkillRun` records boundary status only.
        - Input/output payloads remain API-owned through `SkillRunStep.api_call`.
        - The parent `SkillConfig` is the canonical owner through `SkillConfig.runs`.
        """

        payload = {
            "skill_config_id": skill_config_id,
            "run_key": run_key,
            "status": status,
            "started_at_utc": started_at_utc,
            "finished_at_utc": finished_at_utc,
            "error": error,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_skill_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SkillRun):
            return value
        return SkillRun.validate_invocation_value(value)


class SkillRunCreateStepInput(BaseModel):
    skill_config_step_id: UUID
    api_call_id: UUID | None = Field(default=None)
    status: SkillRunStatus = Field(default=SkillRunStatus.queued)
    started_at_utc: datetime | None = Field(default=None)
    finished_at_utc: datetime | None = Field(default=None)
    error: str | None = Field(default=None)


class SkillRunCreateStepOutput(BaseModel):
    value: SkillRunStep


class SkillRunBuildViaSkillConfigInput(BaseModel):
    skill_config_id: UUID = Field(description="Foreign key for SkillConfig.runs")
    run_key: str
    status: SkillRunStatus = Field(default=SkillRunStatus.queued)
    started_at_utc: datetime | None = Field(default=None)
    finished_at_utc: datetime | None = Field(default=None)
    error: str | None = Field(default=None)


class SkillRunBuildViaSkillConfigOutput(BaseModel):
    value: SkillRun


FUNCTIONS = {
    "SkillRun": {
        "create_step": {
            "canonical": {
                "name": "create_step",
                "description": "Attach one execution receipt for an authored SkillConfigStep.\n\nContract:\n- `skill_config_step_id` is the authored step identity and supplies ordering.\n- `api_call_id` is optional while queued/running/skipped, but terminal invoked steps\n  must attach API-owned call truth at the service/runtime layer.",
                "is_constructor": False,
            },
            "input": SkillRunCreateStepInput,
            "output": SkillRunCreateStepOutput,
        },
        "build_via_skill_config": {
            "canonical": {
                "name": "build_via_skill_config",
                "description": "Create one Skill-owned orchestration run receipt.\n\nContract:\n- `SkillRun` records boundary status only.\n- Input/output payloads remain API-owned through `SkillRunStep.api_call`.\n- The parent `SkillConfig` is the canonical owner through `SkillConfig.runs`.",
                "is_constructor": True,
            },
            "input": SkillRunBuildViaSkillConfigInput,
            "output": SkillRunBuildViaSkillConfigOutput,
        },
    },
}

__all__ = [
    "SkillRun",
    "SkillRunCreateStepInput",
    "SkillRunCreateStepOutput",
    "SkillRunBuildViaSkillConfigInput",
    "SkillRunBuildViaSkillConfigOutput",
    "FUNCTIONS",
]
