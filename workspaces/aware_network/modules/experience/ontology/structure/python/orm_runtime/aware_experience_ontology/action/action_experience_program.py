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
    from aware_experience_ontology.program.program_config import ProgramConfig


class ActionExperienceProgram(ORMModel):
    # Relationships
    program_config: ProgramConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    action_experience_id: UUID = Field(description="Foreign key for ActionExperience.action_experience_programs")
    program_config_id: UUID = Field(description="Foreign key for ActionExperienceProgram.program_config")

    @classmethod
    async def build_via_action_experience(
        cls, action_experience_id: UUID, program_config_id: UUID
    ) -> ActionExperienceProgram:
        """Create a deterministic ActionExperienceProgram association edge."""

        payload = {"action_experience_id": action_experience_id, "program_config_id": program_config_id}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_action_experience", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActionExperienceProgram):
            return value
        return ActionExperienceProgram.validate_invocation_value(value)


class ActionExperienceProgramBuildViaActionExperienceInput(BaseModel):
    action_experience_id: UUID = Field(description="Foreign key for ActionExperience.action_experience_programs")
    program_config_id: UUID


class ActionExperienceProgramBuildViaActionExperienceOutput(BaseModel):
    value: ActionExperienceProgram


FUNCTIONS = {
    "ActionExperienceProgram": {
        "build_via_action_experience": {
            "canonical": {
                "name": "build_via_action_experience",
                "description": "Create a deterministic ActionExperienceProgram association edge.",
                "is_constructor": True,
            },
            "input": ActionExperienceProgramBuildViaActionExperienceInput,
            "output": ActionExperienceProgramBuildViaActionExperienceOutput,
        },
    },
}

__all__ = [
    "ActionExperienceProgram",
    "ActionExperienceProgramBuildViaActionExperienceInput",
    "ActionExperienceProgramBuildViaActionExperienceOutput",
    "FUNCTIONS",
]
