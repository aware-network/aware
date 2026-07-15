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
    from aware_experience_ontology.sensor.sensor_invocation_action import SensorInvocationAction


class Sensor(ORMModel):
    """
    Sensor instance.
    Contract:
    - A Sensor instance is a runtime fulfillment of a Sensor config.
    - It links concrete invocations to the shared Experience invocation spine.
    """

    # Relationships
    invocation_actions: list[SensorInvocationAction] = Field(default_factory=list)

    # Attributes
    sensor_instance_key: str
    external_ref: str | None = Field(default=None)
    status: str = Field(default="active")

    # Foreign Keys
    sensor_config_id: UUID = Field(description="Foreign key for SensorConfig.sensors")

    @classmethod
    async def build_via_sensor_config(
        cls, sensor_config_id: UUID, sensor_instance_key: str, external_ref: str | None = None, status: str = "active"
    ) -> Sensor:
        """
        Create one deterministic Sensor instance under a SensorConfig.

        Contract:
        - Parent `SensorConfig` scope is propagated by constructor lowering.
        - `sensor_instance_key` identifies this runtime fulfillment.
        """

        payload = {
            "sensor_config_id": sensor_config_id,
            "sensor_instance_key": sensor_instance_key,
            "external_ref": external_ref,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_sensor_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Sensor):
            return value
        return Sensor.validate_invocation_value(value)


class SensorBuildViaSensorConfigInput(BaseModel):
    sensor_config_id: UUID = Field(description="Foreign key for SensorConfig.sensors")
    sensor_instance_key: str
    external_ref: str | None = Field(default=None)
    status: str = Field(default="active")


class SensorBuildViaSensorConfigOutput(BaseModel):
    value: Sensor


FUNCTIONS = {
    "Sensor": {
        "build_via_sensor_config": {
            "canonical": {
                "name": "build_via_sensor_config",
                "description": "Create one deterministic Sensor instance under a SensorConfig.\n\nContract:\n- Parent `SensorConfig` scope is propagated by constructor lowering.\n- `sensor_instance_key` identifies this runtime fulfillment.",
                "is_constructor": True,
            },
            "input": SensorBuildViaSensorConfigInput,
            "output": SensorBuildViaSensorConfigOutput,
        },
    },
}

__all__ = [
    "Sensor",
    "SensorBuildViaSensorConfigInput",
    "SensorBuildViaSensorConfigOutput",
    "FUNCTIONS",
]
