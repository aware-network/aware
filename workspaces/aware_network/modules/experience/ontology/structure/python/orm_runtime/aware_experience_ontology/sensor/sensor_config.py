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
    from aware_experience_ontology.sensor.sensor import Sensor
    from aware_experience_ontology.sensor.sensor_config_state_node import SensorConfigStateNode
    from aware_experience_ontology.sensor.sensor_invocation_action_config import SensorInvocationActionConfig


class SensorConfig(ORMModel):
    """
    Sensor configuration.
    Contract:
    - A Sensor config describes inbound information a Connector can observe.
    - Sensor instances are runtime fulfillments declared under this config.
    - Observed state-node footprint declares which Projection nodes this sensor
    observes; payload DTOs are resolved only through invocation bindings.
    - Invocation action config bindings expose the shared Experience invocation
    target surface without duplicating API/SDK/service fields.
    """

    # Relationships
    invocation_action_configs: list[SensorInvocationActionConfig] = Field(default_factory=list)
    observed_state_nodes: list[SensorConfigStateNode] = Field(default_factory=list)
    sensors: list[Sensor] = Field(default_factory=list)

    # Attributes
    sensor_key: str
    sensor_kind: str
    source_ref: str | None = Field(default=None)
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    connector_config_id: UUID = Field(description="Foreign key for ConnectorConfig.sensor_configs")

    async def add_observed_state_node(self, object_projection_graph_node_id: UUID) -> SensorConfigStateNode:
        """
        Add one observed Projection node footprint to this Sensor config.

        Contract:
        - The state node is a Meta ObjectProjectionGraphNode portal.
        - This is not a payload schema. Payload DTO contracts resolve through
          the bound ExperienceInvocationActionConfig endpoint only.
        """

        payload = {"object_projection_graph_node_id": object_projection_graph_node_id}
        result = await invoke_instance(orm_model=self, function_name="add_observed_state_node", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.sensor.sensor_config_state_node import SensorConfigStateNode

        if isinstance(value, SensorConfigStateNode):
            return value
        return SensorConfigStateNode.validate_invocation_value(value)

    async def create_sensor(
        self, sensor_instance_key: str, external_ref: str | None = None, status: str = "active"
    ) -> Sensor:
        """
        Create one deterministic Sensor instance under this Sensor config.

        Contract:
        - Config -> Instance is the canonical ownership rail.
        - Parent `SensorConfig` scope is propagated by constructor lowering.
        - `sensor_instance_key` identifies this runtime fulfillment.
        """

        payload = {"sensor_instance_key": sensor_instance_key, "external_ref": external_ref, "status": status}
        result = await invoke_instance(orm_model=self, function_name="create_sensor", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.sensor.sensor import Sensor

        if isinstance(value, Sensor):
            return value
        return Sensor.validate_invocation_value(value)

    async def bind_invocation_action_config(
        self, experience_invocation_action_config_id: UUID
    ) -> SensorInvocationActionConfig:
        """
        Bind one reusable Experience invocation action config to this Sensor config.

        Contract:
        - `SensorConfig` remains the raw sensor capability surface.
        - `ExperienceInvocationActionConfig` remains the shared target metadata.
        - Sensor instances use the matching action config binding when recording
          concrete invocation provenance.
        """

        payload = {"experience_invocation_action_config_id": experience_invocation_action_config_id}
        result = await invoke_instance(orm_model=self, function_name="bind_invocation_action_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.sensor.sensor_invocation_action_config import SensorInvocationActionConfig

        if isinstance(value, SensorInvocationActionConfig):
            return value
        return SensorInvocationActionConfig.validate_invocation_value(value)

    @classmethod
    async def build_via_connector_config(
        cls,
        connector_config_id: UUID,
        sensor_key: str,
        sensor_kind: str,
        source_ref: str | None = None,
        label: str | None = None,
        description: str | None = None,
    ) -> SensorConfig:
        """
        Create one deterministic Sensor config under a ConnectorConfig.

        Contract:
        - Parent `ConnectorConfig` scope is propagated by constructor lowering.
        - `sensor_key` is stable within the Connector config.
        - `sensor_kind` identifies the inbound event/source family.
        """

        payload = {
            "connector_config_id": connector_config_id,
            "sensor_key": sensor_key,
            "sensor_kind": sensor_kind,
            "source_ref": source_ref,
            "label": label,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_connector_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SensorConfig):
            return value
        return SensorConfig.validate_invocation_value(value)


class SensorConfigAddObservedStateNodeInput(BaseModel):
    object_projection_graph_node_id: UUID


class SensorConfigAddObservedStateNodeOutput(BaseModel):
    value: SensorConfigStateNode


class SensorConfigCreateSensorInput(BaseModel):
    sensor_instance_key: str
    external_ref: str | None = Field(default=None)
    status: str = Field(default="active")


class SensorConfigCreateSensorOutput(BaseModel):
    value: Sensor


class SensorConfigBindInvocationActionConfigInput(BaseModel):
    experience_invocation_action_config_id: UUID


class SensorConfigBindInvocationActionConfigOutput(BaseModel):
    value: SensorInvocationActionConfig


class SensorConfigBuildViaConnectorConfigInput(BaseModel):
    connector_config_id: UUID = Field(description="Foreign key for ConnectorConfig.sensor_configs")
    sensor_key: str
    sensor_kind: str
    source_ref: str | None = Field(default=None)
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)


class SensorConfigBuildViaConnectorConfigOutput(BaseModel):
    value: SensorConfig


FUNCTIONS = {
    "SensorConfig": {
        "add_observed_state_node": {
            "canonical": {
                "name": "add_observed_state_node",
                "description": "Add one observed Projection node footprint to this Sensor config.\n\nContract:\n- The state node is a Meta ObjectProjectionGraphNode portal.\n- This is not a payload schema. Payload DTO contracts resolve through\n  the bound ExperienceInvocationActionConfig endpoint only.",
                "is_constructor": False,
            },
            "input": SensorConfigAddObservedStateNodeInput,
            "output": SensorConfigAddObservedStateNodeOutput,
        },
        "create_sensor": {
            "canonical": {
                "name": "create_sensor",
                "description": "Create one deterministic Sensor instance under this Sensor config.\n\nContract:\n- Config -> Instance is the canonical ownership rail.\n- Parent `SensorConfig` scope is propagated by constructor lowering.\n- `sensor_instance_key` identifies this runtime fulfillment.",
                "is_constructor": False,
            },
            "input": SensorConfigCreateSensorInput,
            "output": SensorConfigCreateSensorOutput,
        },
        "bind_invocation_action_config": {
            "canonical": {
                "name": "bind_invocation_action_config",
                "description": "Bind one reusable Experience invocation action config to this Sensor config.\n\nContract:\n- `SensorConfig` remains the raw sensor capability surface.\n- `ExperienceInvocationActionConfig` remains the shared target metadata.\n- Sensor instances use the matching action config binding when recording\n  concrete invocation provenance.",
                "is_constructor": False,
            },
            "input": SensorConfigBindInvocationActionConfigInput,
            "output": SensorConfigBindInvocationActionConfigOutput,
        },
        "build_via_connector_config": {
            "canonical": {
                "name": "build_via_connector_config",
                "description": "Create one deterministic Sensor config under a ConnectorConfig.\n\nContract:\n- Parent `ConnectorConfig` scope is propagated by constructor lowering.\n- `sensor_key` is stable within the Connector config.\n- `sensor_kind` identifies the inbound event/source family.",
                "is_constructor": True,
            },
            "input": SensorConfigBuildViaConnectorConfigInput,
            "output": SensorConfigBuildViaConnectorConfigOutput,
        },
    },
}

__all__ = [
    "SensorConfig",
    "SensorConfigAddObservedStateNodeInput",
    "SensorConfigAddObservedStateNodeOutput",
    "SensorConfigCreateSensorInput",
    "SensorConfigCreateSensorOutput",
    "SensorConfigBindInvocationActionConfigInput",
    "SensorConfigBindInvocationActionConfigOutput",
    "SensorConfigBuildViaConnectorConfigInput",
    "SensorConfigBuildViaConnectorConfigOutput",
    "FUNCTIONS",
]
