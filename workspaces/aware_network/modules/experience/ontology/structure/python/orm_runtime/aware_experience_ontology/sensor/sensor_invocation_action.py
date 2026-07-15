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
    from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction
    from aware_experience_ontology.sensor.sensor_invocation_action_config import SensorInvocationActionConfig


class SensorInvocationAction(ORMModel):
    """
    Sensor-owned provenance bridge for one concrete invocation action.
    Contract:
    - `SensorInvocationActionConfig` is sensor-level configuration.
    - `ExperienceInvocationAction` is the actual invocation receipt.
    - This bridge records that the invocation happened through one concrete
    Sensor instance.
    """

    # Relationships
    sensor_invocation_action_config: SensorInvocationActionConfig | None = Field(default=None)
    experience_invocation_action: ExperienceInvocationAction | None = Field(default=None)

    # Foreign Keys
    sensor_id: UUID = Field(description="Foreign key for Sensor.invocation_actions")
    sensor_invocation_action_config_id: UUID = Field(
        description="Foreign key for SensorInvocationAction.sensor_invocation_action_config"
    )
    experience_invocation_action_id: UUID = Field(
        description="Foreign key for SensorInvocationAction.experience_invocation_action"
    )

    @classmethod
    async def build(
        cls, sensor_id: UUID, sensor_invocation_action_config_id: UUID, experience_invocation_action_id: UUID
    ) -> SensorInvocationAction:
        """
        Create one deterministic Sensor provenance bridge under a Sensor.

        Contract:
        - `sensor_id` is explicit provenance for the concrete Sensor instance.
        - `sensor_invocation_action_config` proves the action was exposed by
          the Sensor config.
        - `experience_invocation_action` carries the actual invocation receipt.
        """

        payload = {
            "sensor_id": sensor_id,
            "sensor_invocation_action_config_id": sensor_invocation_action_config_id,
            "experience_invocation_action_id": experience_invocation_action_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SensorInvocationAction):
            return value
        return SensorInvocationAction.validate_invocation_value(value)


class SensorInvocationActionBuildInput(BaseModel):
    sensor_id: UUID
    sensor_invocation_action_config_id: UUID
    experience_invocation_action_id: UUID


class SensorInvocationActionBuildOutput(BaseModel):
    value: SensorInvocationAction


FUNCTIONS = {
    "SensorInvocationAction": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one deterministic Sensor provenance bridge under a Sensor.\n\nContract:\n- `sensor_id` is explicit provenance for the concrete Sensor instance.\n- `sensor_invocation_action_config` proves the action was exposed by\n  the Sensor config.\n- `experience_invocation_action` carries the actual invocation receipt.",
                "is_constructor": True,
            },
            "input": SensorInvocationActionBuildInput,
            "output": SensorInvocationActionBuildOutput,
        },
    },
}

__all__ = [
    "SensorInvocationAction",
    "SensorInvocationActionBuildInput",
    "SensorInvocationActionBuildOutput",
    "FUNCTIONS",
]
