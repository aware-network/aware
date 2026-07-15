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
    from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction
    from aware_experience_ontology.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )


class SensorInvocationActionConfig(ORMModel):
    """
    Sensor-owned binding to one generic Experience invocation action config.
    Contract:
    - A Sensor config can expose one or more reusable invocation action targets.
    - API/SDK/service target metadata lives on `ExperienceInvocationActionConfig`.
    - Actual invocation receipts are linked to concrete Sensor instances by
    `SensorInvocationAction`.
    """

    # Relationships
    experience_invocation_action_config: ExperienceInvocationActionConfig | None = Field(default=None)

    # Foreign Keys
    sensor_config_id: UUID = Field(description="Foreign key for SensorConfig.invocation_action_configs")
    experience_invocation_action_config_id: UUID = Field(
        description="Foreign key for SensorInvocationActionConfig.experience_invocation_action_config"
    )

    async def record_invocation(
        self,
        invocation_key: UUID,
        actor_id: UUID | None = None,
        api_call_id: UUID | None = None,
        sdk_operation_call_id: UUID | None = None,
        request_ref: str | None = None,
        receipt_ref: str | None = None,
        status: str = "pending",
    ) -> ExperienceInvocationAction:
        """
        Record one actual invocation handled through this sensor action config.

        Contract:
        - Parentage is `SensorConfig -> SensorInvocationActionConfig`.
        - `ExperienceInvocationActionConfig` remains target metadata only.
        - Concrete Sensor instance provenance is recorded by `SensorInvocationAction`,
          which links to the actual Experience invocation receipt.
        """

        payload = {
            "invocation_key": invocation_key,
            "actor_id": actor_id,
            "api_call_id": api_call_id,
            "sdk_operation_call_id": sdk_operation_call_id,
            "request_ref": request_ref,
            "receipt_ref": receipt_ref,
            "status": status,
        }
        result = await invoke_instance(orm_model=self, function_name="record_invocation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction

        if isinstance(value, ExperienceInvocationAction):
            return value
        return ExperienceInvocationAction.validate_invocation_value(value)

    @classmethod
    async def build_via_sensor_config(
        cls, sensor_config_id: UUID, experience_invocation_action_config_id: UUID
    ) -> SensorInvocationActionConfig:
        """
        Bind one generic invocation action config under a SensorConfig.

        Contract:
        - Parent `SensorConfig` scope is propagated by constructor lowering.
        - This object only says that the sensor config can invoke that reusable
          Experience action target.
        """

        payload = {
            "sensor_config_id": sensor_config_id,
            "experience_invocation_action_config_id": experience_invocation_action_config_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_sensor_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SensorInvocationActionConfig):
            return value
        return SensorInvocationActionConfig.validate_invocation_value(value)


class SensorInvocationActionConfigRecordInvocationInput(BaseModel):
    invocation_key: UUID
    actor_id: UUID | None = Field(default=None)
    api_call_id: UUID | None = Field(default=None)
    sdk_operation_call_id: UUID | None = Field(default=None)
    request_ref: str | None = Field(default=None)
    receipt_ref: str | None = Field(default=None)
    status: str = Field(default="pending")


class SensorInvocationActionConfigRecordInvocationOutput(BaseModel):
    value: ExperienceInvocationAction


class SensorInvocationActionConfigBuildViaSensorConfigInput(BaseModel):
    sensor_config_id: UUID = Field(description="Foreign key for SensorConfig.invocation_action_configs")
    experience_invocation_action_config_id: UUID


class SensorInvocationActionConfigBuildViaSensorConfigOutput(BaseModel):
    value: SensorInvocationActionConfig


FUNCTIONS = {
    "SensorInvocationActionConfig": {
        "record_invocation": {
            "canonical": {
                "name": "record_invocation",
                "description": "Record one actual invocation handled through this sensor action config.\n\nContract:\n- Parentage is `SensorConfig -> SensorInvocationActionConfig`.\n- `ExperienceInvocationActionConfig` remains target metadata only.\n- Concrete Sensor instance provenance is recorded by `SensorInvocationAction`,\n  which links to the actual Experience invocation receipt.",
                "is_constructor": False,
            },
            "input": SensorInvocationActionConfigRecordInvocationInput,
            "output": SensorInvocationActionConfigRecordInvocationOutput,
        },
        "build_via_sensor_config": {
            "canonical": {
                "name": "build_via_sensor_config",
                "description": "Bind one generic invocation action config under a SensorConfig.\n\nContract:\n- Parent `SensorConfig` scope is propagated by constructor lowering.\n- This object only says that the sensor config can invoke that reusable\n  Experience action target.",
                "is_constructor": True,
            },
            "input": SensorInvocationActionConfigBuildViaSensorConfigInput,
            "output": SensorInvocationActionConfigBuildViaSensorConfigOutput,
        },
    },
}

__all__ = [
    "SensorInvocationActionConfig",
    "SensorInvocationActionConfigRecordInvocationInput",
    "SensorInvocationActionConfigRecordInvocationOutput",
    "SensorInvocationActionConfigBuildViaSensorConfigInput",
    "SensorInvocationActionConfigBuildViaSensorConfigOutput",
    "FUNCTIONS",
]
