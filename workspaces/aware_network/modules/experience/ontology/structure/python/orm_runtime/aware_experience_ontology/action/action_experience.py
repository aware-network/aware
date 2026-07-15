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
    from aware_experience_ontology.action.action_experience_invocation import ActionExperienceInvocation
    from aware_experience_ontology.action.action_experience_program import ActionExperienceProgram
    from aware_reactivity_ontology.action.action_config import ActionConfig


class ActionExperience(ORMModel):
    # Relationships
    action_config: ActionConfig | None = Field(default=None, exclude=True)
    action_experience_programs: list[ActionExperienceProgram] = Field(default_factory=list, exclude=True)
    action_experience_invocations: list[ActionExperienceInvocation] = Field(default_factory=list, exclude=True)

    # Foreign Keys
    action_config_id: UUID = Field(description="Foreign key for ActionExperience.action_config")

    @classmethod
    async def build(cls, action_config_id: UUID) -> ActionExperience:
        """
        Create a deterministic ActionExperience association edge with associated program configs.

        Contract:
        - ActionExperience identity is scoped by `action_config_id`.
        - Thread-scoped program availability belongs under
          EnvironmentExperienceThreadConfig, not a hidden action parent context.
        """

        payload = {"action_config_id": action_config_id}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActionExperience):
            return value
        return ActionExperience.validate_invocation_value(value)

    async def add_program_config(self, program_config_id: UUID) -> ActionExperienceProgram:
        """Add a program config to the action experience."""

        payload = {"program_config_id": program_config_id}
        result = await invoke_instance(orm_model=self, function_name="add_program_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.action.action_experience_program import ActionExperienceProgram

        if isinstance(value, ActionExperienceProgram):
            return value
        return ActionExperienceProgram.validate_invocation_value(value)

    async def add_invocation_action_config(
        self, experience_invocation_action_config_id: UUID
    ) -> ActionExperienceInvocation:
        """
        Bind an Experience invocation action config to this action experience.

        Contract:
        - Reactivity stays API-agnostic; this edge lives in Experience.
        - Dispatch-time selection among many invocation configs is a later
          concern.
        - The bound ExperienceInvocationActionConfig resolves the typed
          request/response/stream contract through API/SDK target metadata.
        """

        payload = {"experience_invocation_action_config_id": experience_invocation_action_config_id}
        result = await invoke_instance(orm_model=self, function_name="add_invocation_action_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.action.action_experience_invocation import ActionExperienceInvocation

        if isinstance(value, ActionExperienceInvocation):
            return value
        return ActionExperienceInvocation.validate_invocation_value(value)


class ActionExperienceBuildInput(BaseModel):
    action_config_id: UUID


class ActionExperienceBuildOutput(BaseModel):
    value: ActionExperience


class ActionExperienceAddProgramConfigInput(BaseModel):
    program_config_id: UUID


class ActionExperienceAddProgramConfigOutput(BaseModel):
    value: ActionExperienceProgram


class ActionExperienceAddInvocationActionConfigInput(BaseModel):
    experience_invocation_action_config_id: UUID


class ActionExperienceAddInvocationActionConfigOutput(BaseModel):
    value: ActionExperienceInvocation


FUNCTIONS = {
    "ActionExperience": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create a deterministic ActionExperience association edge with associated program configs.\n\nContract:\n- ActionExperience identity is scoped by `action_config_id`.\n- Thread-scoped program availability belongs under\n  EnvironmentExperienceThreadConfig, not a hidden action parent context.",
                "is_constructor": True,
            },
            "input": ActionExperienceBuildInput,
            "output": ActionExperienceBuildOutput,
        },
        "add_program_config": {
            "canonical": {
                "name": "add_program_config",
                "description": "Add a program config to the action experience.",
                "is_constructor": False,
            },
            "input": ActionExperienceAddProgramConfigInput,
            "output": ActionExperienceAddProgramConfigOutput,
        },
        "add_invocation_action_config": {
            "canonical": {
                "name": "add_invocation_action_config",
                "description": "Bind an Experience invocation action config to this action experience.\n\nContract:\n- Reactivity stays API-agnostic; this edge lives in Experience.\n- Dispatch-time selection among many invocation configs is a later\n  concern.\n- The bound ExperienceInvocationActionConfig resolves the typed\n  request/response/stream contract through API/SDK target metadata.",
                "is_constructor": False,
            },
            "input": ActionExperienceAddInvocationActionConfigInput,
            "output": ActionExperienceAddInvocationActionConfigOutput,
        },
    },
}

__all__ = [
    "ActionExperience",
    "ActionExperienceBuildInput",
    "ActionExperienceBuildOutput",
    "ActionExperienceAddProgramConfigInput",
    "ActionExperienceAddProgramConfigOutput",
    "ActionExperienceAddInvocationActionConfigInput",
    "ActionExperienceAddInvocationActionConfigOutput",
    "FUNCTIONS",
]
