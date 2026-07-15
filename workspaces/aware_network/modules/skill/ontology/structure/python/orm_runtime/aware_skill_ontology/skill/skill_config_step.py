from __future__ import annotations

# Standard
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

if TYPE_CHECKING:
    from aware_skill_ontology.skill.skill_config_api_endpoint import SkillConfigApiEndpoint
    from aware_skill_ontology.skill.skill_config_step_target import SkillConfigStepTarget


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

    async def add_target(self, skill_config_target_id: UUID, description: str | None = None) -> SkillConfigStepTarget:
        """
        Bind one Experience-owned authored Skill target to this step.

        Contract:
        - A step may bind zero, one, or many SkillConfigTarget rows.
        - Each target resolves through Experience-owned graph identity truth.
        - The step API endpoint requirement remains on `SkillConfigApiEndpoint`.
        """

        payload = {"skill_config_target_id": skill_config_target_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="add_target", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_skill_ontology.skill.skill_config_step_target import SkillConfigStepTarget

        if isinstance(value, SkillConfigStepTarget):
            return value
        return SkillConfigStepTarget.validate_invocation_value(value)

    @classmethod
    async def build_via_skill_config(
        cls, skill_config_id: UUID, position: int, skill_config_api_endpoint_id: UUID, instruction: str
    ) -> SkillConfigStep:
        """
        Create one ordered step in a Skill orchestration plan.

        Contract:
        - A step binds to Skill-owned `SkillConfigApiEndpoint` requirement truth.
        - API-owned endpoint invocation details remain downstream runtime/service concerns.
        """

        payload = {
            "skill_config_id": skill_config_id,
            "position": position,
            "skill_config_api_endpoint_id": skill_config_api_endpoint_id,
            "instruction": instruction,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_skill_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SkillConfigStep):
            return value
        return SkillConfigStep.validate_invocation_value(value)


class SkillConfigStepAddTargetInput(BaseModel):
    skill_config_target_id: UUID
    description: str | None = Field(default=None)


class SkillConfigStepAddTargetOutput(BaseModel):
    value: SkillConfigStepTarget


class SkillConfigStepBuildViaSkillConfigInput(BaseModel):
    skill_config_id: UUID = Field(description="Foreign key for SkillConfig.steps")
    position: int
    skill_config_api_endpoint_id: UUID
    instruction: str


class SkillConfigStepBuildViaSkillConfigOutput(BaseModel):
    value: SkillConfigStep


FUNCTIONS = {
    "SkillConfigStep": {
        "add_target": {
            "canonical": {
                "name": "add_target",
                "description": "Bind one Experience-owned authored Skill target to this step.\n\nContract:\n- A step may bind zero, one, or many SkillConfigTarget rows.\n- Each target resolves through Experience-owned graph identity truth.\n- The step API endpoint requirement remains on `SkillConfigApiEndpoint`.",
                "is_constructor": False,
            },
            "input": SkillConfigStepAddTargetInput,
            "output": SkillConfigStepAddTargetOutput,
        },
        "build_via_skill_config": {
            "canonical": {
                "name": "build_via_skill_config",
                "description": "Create one ordered step in a Skill orchestration plan.\n\nContract:\n- A step binds to Skill-owned `SkillConfigApiEndpoint` requirement truth.\n- API-owned endpoint invocation details remain downstream runtime/service concerns.",
                "is_constructor": True,
            },
            "input": SkillConfigStepBuildViaSkillConfigInput,
            "output": SkillConfigStepBuildViaSkillConfigOutput,
        },
    },
}

__all__ = [
    "SkillConfigStep",
    "SkillConfigStepAddTargetInput",
    "SkillConfigStepAddTargetOutput",
    "SkillConfigStepBuildViaSkillConfigInput",
    "SkillConfigStepBuildViaSkillConfigOutput",
    "FUNCTIONS",
]
