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
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_skill_ontology.skill.skill_config_target import SkillConfigTarget


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

    @classmethod
    async def build_via_skill_config_step(
        cls, skill_config_step_id: UUID, skill_config_target_id: UUID, description: str | None = None
    ) -> SkillConfigStepTarget:
        """
        Create one Skill-owned binding between a Skill step and an Experience target.

        Contract:
        - `skill_config_target` is Skill/Experience-owned semantic target selection.
        - The parent `SkillConfigStep` owns API endpoint intent through `SkillConfigApiEndpoint`.
        - API calls remain payload truth; Service remains downstream fulfillment truth.
        """

        payload = {
            "skill_config_step_id": skill_config_step_id,
            "skill_config_target_id": skill_config_target_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_skill_config_step", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SkillConfigStepTarget):
            return value
        return SkillConfigStepTarget.validate_invocation_value(value)


class SkillConfigStepTargetBuildViaSkillConfigStepInput(BaseModel):
    skill_config_step_id: UUID = Field(description="Foreign key for SkillConfigStep.targets")
    skill_config_target_id: UUID
    description: str | None = Field(default=None)


class SkillConfigStepTargetBuildViaSkillConfigStepOutput(BaseModel):
    value: SkillConfigStepTarget


FUNCTIONS = {
    "SkillConfigStepTarget": {
        "build_via_skill_config_step": {
            "canonical": {
                "name": "build_via_skill_config_step",
                "description": "Create one Skill-owned binding between a Skill step and an Experience target.\n\nContract:\n- `skill_config_target` is Skill/Experience-owned semantic target selection.\n- The parent `SkillConfigStep` owns API endpoint intent through `SkillConfigApiEndpoint`.\n- API calls remain payload truth; Service remains downstream fulfillment truth.",
                "is_constructor": True,
            },
            "input": SkillConfigStepTargetBuildViaSkillConfigStepInput,
            "output": SkillConfigStepTargetBuildViaSkillConfigStepOutput,
        },
    },
}

__all__ = [
    "SkillConfigStepTarget",
    "SkillConfigStepTargetBuildViaSkillConfigStepInput",
    "SkillConfigStepTargetBuildViaSkillConfigStepOutput",
    "FUNCTIONS",
]
