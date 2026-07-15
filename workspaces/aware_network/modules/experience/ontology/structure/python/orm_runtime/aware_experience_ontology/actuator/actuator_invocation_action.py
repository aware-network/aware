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
    from aware_experience_ontology.actuator.actuator_invocation_action_config import ActuatorInvocationActionConfig
    from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction


class ActuatorInvocationAction(ORMModel):
    """
    Actuator-owned provenance bridge for one concrete invocation action.
    Contract:
    - `ActuatorInvocationActionConfig` is actuator-level configuration.
    - `ExperienceInvocationAction` is the actual invocation receipt.
    - This bridge records that the invocation happened through one concrete
    Actuator instance.
    """

    # Relationships
    actuator_invocation_action_config: ActuatorInvocationActionConfig | None = Field(default=None)
    experience_invocation_action: ExperienceInvocationAction | None = Field(default=None)

    # Foreign Keys
    actuator_id: UUID = Field(description="Foreign key for Actuator.invocation_actions")
    actuator_invocation_action_config_id: UUID = Field(
        description="Foreign key for ActuatorInvocationAction.actuator_invocation_action_config"
    )
    experience_invocation_action_id: UUID = Field(
        description="Foreign key for ActuatorInvocationAction.experience_invocation_action"
    )

    @classmethod
    async def build(
        cls, actuator_id: UUID, actuator_invocation_action_config_id: UUID, experience_invocation_action_id: UUID
    ) -> ActuatorInvocationAction:
        """
        Create one deterministic Actuator provenance bridge under an Actuator.

        Contract:
        - `actuator_id` is explicit provenance for the concrete Actuator instance.
        - `actuator_invocation_action_config` proves the action was exposed by
          the Actuator config.
        - `experience_invocation_action` carries the actual invocation receipt.
        """

        payload = {
            "actuator_id": actuator_id,
            "actuator_invocation_action_config_id": actuator_invocation_action_config_id,
            "experience_invocation_action_id": experience_invocation_action_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActuatorInvocationAction):
            return value
        return ActuatorInvocationAction.validate_invocation_value(value)


class ActuatorInvocationActionBuildInput(BaseModel):
    actuator_id: UUID
    actuator_invocation_action_config_id: UUID
    experience_invocation_action_id: UUID


class ActuatorInvocationActionBuildOutput(BaseModel):
    value: ActuatorInvocationAction


FUNCTIONS = {
    "ActuatorInvocationAction": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one deterministic Actuator provenance bridge under an Actuator.\n\nContract:\n- `actuator_id` is explicit provenance for the concrete Actuator instance.\n- `actuator_invocation_action_config` proves the action was exposed by\n  the Actuator config.\n- `experience_invocation_action` carries the actual invocation receipt.",
                "is_constructor": True,
            },
            "input": ActuatorInvocationActionBuildInput,
            "output": ActuatorInvocationActionBuildOutput,
        },
    },
}

__all__ = [
    "ActuatorInvocationAction",
    "ActuatorInvocationActionBuildInput",
    "ActuatorInvocationActionBuildOutput",
    "FUNCTIONS",
]
