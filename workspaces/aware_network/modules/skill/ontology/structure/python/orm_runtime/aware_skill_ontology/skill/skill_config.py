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
    from aware_skill_ontology.skill.skill_config_api import SkillConfigApi
    from aware_skill_ontology.skill.skill_config_experience import SkillConfigExperience
    from aware_skill_ontology.skill.skill_config_step import SkillConfigStep
    from aware_skill_ontology.skill.skill_run import SkillRun


class SkillConfig(ORMModel):
    # Relationships
    apis: list[SkillConfigApi] = Field(default_factory=list)
    experiences: list[SkillConfigExperience] = Field(default_factory=list)
    runs: list[SkillRun] = Field(default_factory=list, exclude=True)
    steps: list[SkillConfigStep] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    name: str

    @classmethod
    async def build(cls, name: str, description: str | None = None) -> SkillConfig:
        """
        Create one canonical reusable Skill definition.

        Contract:
        - `SkillConfig` is the semantic orchestration root.
        - `SkillConfigApi` groups API-scoped endpoint requirements for this Skill.
        - `SkillConfigApiEndpoint` binds to API-owned endpoint invocation truth through the Api projection.
        - Runtime execution/service overlays are later layers, not owned by this config.
        """

        payload = {"name": name, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SkillConfig):
            return value
        return SkillConfig.validate_invocation_value(value)

    async def add_api(self, api_id: UUID, description: str | None = None) -> SkillConfigApi:
        """Add one API grouping available to this Skill."""

        payload = {"api_id": api_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="add_api", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_skill_ontology.skill.skill_config_api import SkillConfigApi

        if isinstance(value, SkillConfigApi):
            return value
        return SkillConfigApi.validate_invocation_value(value)

    async def add_step(self, position: int, skill_config_api_endpoint_id: UUID, instruction: str) -> SkillConfigStep:
        """Add one ordered orchestration step bound to one Skill-owned API endpoint requirement."""

        payload = {
            "position": position,
            "skill_config_api_endpoint_id": skill_config_api_endpoint_id,
            "instruction": instruction,
        }
        result = await invoke_instance(orm_model=self, function_name="add_step", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_skill_ontology.skill.skill_config_step import SkillConfigStep

        if isinstance(value, SkillConfigStep):
            return value
        return SkillConfigStep.validate_invocation_value(value)

    async def add_experience(
        self, projection_experience_id: UUID, description: str | None = None
    ) -> SkillConfigExperience:
        """
        Add one Experience graph namespace this SkillConfig may target.

        Contract:
        - Skill targets remain authored Skill-owned truth.
        - Experience owns graph identity/profile resolution.
        """

        payload = {"projection_experience_id": projection_experience_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="add_experience", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_skill_ontology.skill.skill_config_experience import SkillConfigExperience

        if isinstance(value, SkillConfigExperience):
            return value
        return SkillConfigExperience.validate_invocation_value(value)

    async def create_run(
        self,
        run_key: str,
        status: SkillRunStatus = SkillRunStatus.queued,
        started_at_utc: datetime | None = None,
        finished_at_utc: datetime | None = None,
        error: str | None = None,
    ) -> SkillRun:
        """
        Create one canonical execution receipt for this SkillConfig.

        Contract:
        - `SkillRun` is Skill-owned orchestration status truth.
        - Request/response payload truth remains owned by API through `ApiCall`.
        - Run steps are tracked as `SkillRunStep` receipts keyed to authored `SkillConfigStep` truth.
        """

        payload = {
            "run_key": run_key,
            "status": status,
            "started_at_utc": started_at_utc,
            "finished_at_utc": finished_at_utc,
            "error": error,
        }
        result = await invoke_instance(orm_model=self, function_name="create_run", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_skill_ontology.skill.skill_run import SkillRun

        if isinstance(value, SkillRun):
            return value
        return SkillRun.validate_invocation_value(value)


class SkillConfigBuildInput(BaseModel):
    name: str
    description: str | None = Field(default=None)


class SkillConfigBuildOutput(BaseModel):
    value: SkillConfig


class SkillConfigAddApiInput(BaseModel):
    api_id: UUID
    description: str | None = Field(default=None)


class SkillConfigAddApiOutput(BaseModel):
    value: SkillConfigApi


class SkillConfigAddStepInput(BaseModel):
    position: int
    skill_config_api_endpoint_id: UUID
    instruction: str


class SkillConfigAddStepOutput(BaseModel):
    value: SkillConfigStep


class SkillConfigAddExperienceInput(BaseModel):
    projection_experience_id: UUID
    description: str | None = Field(default=None)


class SkillConfigAddExperienceOutput(BaseModel):
    value: SkillConfigExperience


class SkillConfigCreateRunInput(BaseModel):
    run_key: str
    status: SkillRunStatus = Field(default=SkillRunStatus.queued)
    started_at_utc: datetime | None = Field(default=None)
    finished_at_utc: datetime | None = Field(default=None)
    error: str | None = Field(default=None)


class SkillConfigCreateRunOutput(BaseModel):
    value: SkillRun


FUNCTIONS = {
    "SkillConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one canonical reusable Skill definition.\n\nContract:\n- `SkillConfig` is the semantic orchestration root.\n- `SkillConfigApi` groups API-scoped endpoint requirements for this Skill.\n- `SkillConfigApiEndpoint` binds to API-owned endpoint invocation truth through the Api projection.\n- Runtime execution/service overlays are later layers, not owned by this config.",
                "is_constructor": True,
            },
            "input": SkillConfigBuildInput,
            "output": SkillConfigBuildOutput,
        },
        "add_api": {
            "canonical": {
                "name": "add_api",
                "description": "Add one API grouping available to this Skill.",
                "is_constructor": False,
            },
            "input": SkillConfigAddApiInput,
            "output": SkillConfigAddApiOutput,
        },
        "add_step": {
            "canonical": {
                "name": "add_step",
                "description": "Add one ordered orchestration step bound to one Skill-owned API endpoint requirement.",
                "is_constructor": False,
            },
            "input": SkillConfigAddStepInput,
            "output": SkillConfigAddStepOutput,
        },
        "add_experience": {
            "canonical": {
                "name": "add_experience",
                "description": "Add one Experience graph namespace this SkillConfig may target.\n\nContract:\n- Skill targets remain authored Skill-owned truth.\n- Experience owns graph identity/profile resolution.",
                "is_constructor": False,
            },
            "input": SkillConfigAddExperienceInput,
            "output": SkillConfigAddExperienceOutput,
        },
        "create_run": {
            "canonical": {
                "name": "create_run",
                "description": "Create one canonical execution receipt for this SkillConfig.\n\nContract:\n- `SkillRun` is Skill-owned orchestration status truth.\n- Request/response payload truth remains owned by API through `ApiCall`.\n- Run steps are tracked as `SkillRunStep` receipts keyed to authored `SkillConfigStep` truth.",
                "is_constructor": False,
            },
            "input": SkillConfigCreateRunInput,
            "output": SkillConfigCreateRunOutput,
        },
    },
}

__all__ = [
    "SkillConfig",
    "SkillConfigBuildInput",
    "SkillConfigBuildOutput",
    "SkillConfigAddApiInput",
    "SkillConfigAddApiOutput",
    "SkillConfigAddStepInput",
    "SkillConfigAddStepOutput",
    "SkillConfigAddExperienceInput",
    "SkillConfigAddExperienceOutput",
    "SkillConfigCreateRunInput",
    "SkillConfigCreateRunOutput",
    "FUNCTIONS",
]
