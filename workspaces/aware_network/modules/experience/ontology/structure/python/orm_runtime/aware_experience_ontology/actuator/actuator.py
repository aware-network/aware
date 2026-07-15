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
    from aware_experience_ontology.actuator.actuator_invocation_action import ActuatorInvocationAction


class Actuator(ORMModel):
    """
    Actuator instance.
    Contract:
    - An Actuator instance is a runtime fulfillment of an Actuator config.
    - It links concrete invocations to the shared Experience invocation spine.
    """

    # Relationships
    invocation_actions: list[ActuatorInvocationAction] = Field(default_factory=list)

    # Attributes
    actuator_instance_key: str
    external_ref: str | None = Field(default=None)
    status: str = Field(default="active")

    # Foreign Keys
    actuator_config_id: UUID = Field(description="Foreign key for ActuatorConfig.actuators")

    @classmethod
    async def build_via_actuator_config(
        cls,
        actuator_config_id: UUID,
        actuator_instance_key: str,
        external_ref: str | None = None,
        status: str = "active",
    ) -> Actuator:
        """
        Create one deterministic Actuator instance under an ActuatorConfig.

        Contract:
        - Parent `ActuatorConfig` scope is propagated by constructor lowering.
        - `actuator_instance_key` identifies this runtime fulfillment.
        """

        payload = {
            "actuator_config_id": actuator_config_id,
            "actuator_instance_key": actuator_instance_key,
            "external_ref": external_ref,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_actuator_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Actuator):
            return value
        return Actuator.validate_invocation_value(value)


class ActuatorBuildViaActuatorConfigInput(BaseModel):
    actuator_config_id: UUID = Field(description="Foreign key for ActuatorConfig.actuators")
    actuator_instance_key: str
    external_ref: str | None = Field(default=None)
    status: str = Field(default="active")


class ActuatorBuildViaActuatorConfigOutput(BaseModel):
    value: Actuator


FUNCTIONS = {
    "Actuator": {
        "build_via_actuator_config": {
            "canonical": {
                "name": "build_via_actuator_config",
                "description": "Create one deterministic Actuator instance under an ActuatorConfig.\n\nContract:\n- Parent `ActuatorConfig` scope is propagated by constructor lowering.\n- `actuator_instance_key` identifies this runtime fulfillment.",
                "is_constructor": True,
            },
            "input": ActuatorBuildViaActuatorConfigInput,
            "output": ActuatorBuildViaActuatorConfigOutput,
        },
    },
}

__all__ = [
    "Actuator",
    "ActuatorBuildViaActuatorConfigInput",
    "ActuatorBuildViaActuatorConfigOutput",
    "FUNCTIONS",
]
