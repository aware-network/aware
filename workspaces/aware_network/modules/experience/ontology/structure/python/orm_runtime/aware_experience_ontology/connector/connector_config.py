from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

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
    from aware_experience_ontology.actuator.actuator_config import ActuatorConfig
    from aware_experience_ontology.connector.connector import Connector
    from aware_experience_ontology.connector.connector_provider import ConnectorProvider
    from aware_experience_ontology.sensor.sensor_config import SensorConfig


class ConnectorConfig(ORMModel):
    """
    Connector configuration.
    Contract:
    - A Connector config describes one external integration capability family.
    - Provider configs distinguish concrete external products/vendors for the
    same capability family.
    - Sensor and Actuator configs are declared under the Connector config.
    - Connector instances are runtime fulfillments declared under this config.
    - Experience-specific attachment and invocation-action bridges are deferred.
    """

    # Relationships
    providers: list[ConnectorProvider] = Field(default_factory=list)
    sensor_configs: list[SensorConfig] = Field(default_factory=list)
    actuator_configs: list[ActuatorConfig] = Field(default_factory=list)
    connectors: list[Connector] = Field(default_factory=list)

    # Attributes
    connector_key: str
    connector_kind: str
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)

    @classmethod
    async def create(
        cls, connector_key: str, connector_kind: str, label: str | None = None, description: str | None = None
    ) -> ConnectorConfig:
        """
        Create one canonical Connector config root.

        Contract:
        - `connector_key` is the stable service-facing config key.
        - `connector_kind` identifies the integration family.
        - The config is not scoped to a ProjectionExperience.
        """

        payload = {
            "connector_key": connector_key,
            "connector_kind": connector_kind,
            "label": label,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ConnectorConfig):
            return value
        return ConnectorConfig.validate_invocation_value(value)

    async def add_provider(
        self,
        provider_key: str,
        provider_kind: str,
        provider_ref: str | None = None,
        label: str | None = None,
        description: str | None = None,
    ) -> ConnectorProvider:
        """
        Add one provider config under this Connector config.

        Contract:
        - `ConnectorConfig` is the capability family, e.g. music.
        - `ConnectorProvider` is the concrete external provider, e.g.
          youtube_music or spotify.
        - Runtime session identity is owned by `ConnectorSession`, not the
          reusable provider config.
        """

        payload = {
            "provider_key": provider_key,
            "provider_kind": provider_kind,
            "provider_ref": provider_ref,
            "label": label,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="add_provider", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.connector.connector_provider import ConnectorProvider

        if isinstance(value, ConnectorProvider):
            return value
        return ConnectorProvider.validate_invocation_value(value)

    async def add_sensor_config(
        self,
        sensor_key: str,
        sensor_kind: str,
        source_ref: str | None = None,
        label: str | None = None,
        description: str | None = None,
    ) -> SensorConfig:
        """
        Add one Sensor config to this Connector config.

        Contract:
        - Sensors model inbound external information observed by this connector.
        - `source_ref` is a deferred adapter-facing instance hint.
        - Projection-node footprint is declared under SensorConfig state nodes.
        """

        payload = {
            "sensor_key": sensor_key,
            "sensor_kind": sensor_kind,
            "source_ref": source_ref,
            "label": label,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="add_sensor_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.sensor.sensor_config import SensorConfig

        if isinstance(value, SensorConfig):
            return value
        return SensorConfig.validate_invocation_value(value)

    async def add_actuator_config(
        self,
        actuator_key: str,
        actuator_kind: str,
        target_ref: str | None = None,
        label: str | None = None,
        description: str | None = None,
    ) -> ActuatorConfig:
        """
        Add one Actuator config to this Connector config.

        Contract:
        - Actuators model outbound actions this connector can perform.
        - `target_ref` is a deferred adapter-facing instance hint.
        - Projection-node footprint is declared under ActuatorConfig state nodes.
        """

        payload = {
            "actuator_key": actuator_key,
            "actuator_kind": actuator_kind,
            "target_ref": target_ref,
            "label": label,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="add_actuator_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.actuator.actuator_config import ActuatorConfig

        if isinstance(value, ActuatorConfig):
            return value
        return ActuatorConfig.validate_invocation_value(value)

    async def create_connector(
        self, connector_instance_key: str, runtime_ref: str | None = None, status: str = "active"
    ) -> Connector:
        """
        Create one deterministic Connector instance under this Connector config.

        Contract:
        - Config -> Instance is the canonical ownership rail.
        - Parent `ConnectorConfig` scope is propagated by constructor lowering.
        - `connector_instance_key` identifies this runtime fulfillment.
        """

        payload = {"connector_instance_key": connector_instance_key, "runtime_ref": runtime_ref, "status": status}
        result = await invoke_instance(orm_model=self, function_name="create_connector", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.connector.connector import Connector

        if isinstance(value, Connector):
            return value
        return Connector.validate_invocation_value(value)


class ConnectorConfigCreateInput(BaseModel):
    connector_key: str
    connector_kind: str
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ConnectorConfigCreateOutput(BaseModel):
    value: ConnectorConfig


class ConnectorConfigAddProviderInput(BaseModel):
    provider_key: str
    provider_kind: str
    provider_ref: str | None = Field(default=None)
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ConnectorConfigAddProviderOutput(BaseModel):
    value: ConnectorProvider


class ConnectorConfigAddSensorConfigInput(BaseModel):
    sensor_key: str
    sensor_kind: str
    source_ref: str | None = Field(default=None)
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ConnectorConfigAddSensorConfigOutput(BaseModel):
    value: SensorConfig


class ConnectorConfigAddActuatorConfigInput(BaseModel):
    actuator_key: str
    actuator_kind: str
    target_ref: str | None = Field(default=None)
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ConnectorConfigAddActuatorConfigOutput(BaseModel):
    value: ActuatorConfig


class ConnectorConfigCreateConnectorInput(BaseModel):
    connector_instance_key: str
    runtime_ref: str | None = Field(default=None)
    status: str = Field(default="active")


class ConnectorConfigCreateConnectorOutput(BaseModel):
    value: Connector


FUNCTIONS = {
    "ConnectorConfig": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create one canonical Connector config root.\n\nContract:\n- `connector_key` is the stable service-facing config key.\n- `connector_kind` identifies the integration family.\n- The config is not scoped to a ProjectionExperience.",
                "is_constructor": True,
            },
            "input": ConnectorConfigCreateInput,
            "output": ConnectorConfigCreateOutput,
        },
        "add_provider": {
            "canonical": {
                "name": "add_provider",
                "description": "Add one provider config under this Connector config.\n\nContract:\n- `ConnectorConfig` is the capability family, e.g. music.\n- `ConnectorProvider` is the concrete external provider, e.g.\n  youtube_music or spotify.\n- Runtime session identity is owned by `ConnectorSession`, not the\n  reusable provider config.",
                "is_constructor": False,
            },
            "input": ConnectorConfigAddProviderInput,
            "output": ConnectorConfigAddProviderOutput,
        },
        "add_sensor_config": {
            "canonical": {
                "name": "add_sensor_config",
                "description": "Add one Sensor config to this Connector config.\n\nContract:\n- Sensors model inbound external information observed by this connector.\n- `source_ref` is a deferred adapter-facing instance hint.\n- Projection-node footprint is declared under SensorConfig state nodes.",
                "is_constructor": False,
            },
            "input": ConnectorConfigAddSensorConfigInput,
            "output": ConnectorConfigAddSensorConfigOutput,
        },
        "add_actuator_config": {
            "canonical": {
                "name": "add_actuator_config",
                "description": "Add one Actuator config to this Connector config.\n\nContract:\n- Actuators model outbound actions this connector can perform.\n- `target_ref` is a deferred adapter-facing instance hint.\n- Projection-node footprint is declared under ActuatorConfig state nodes.",
                "is_constructor": False,
            },
            "input": ConnectorConfigAddActuatorConfigInput,
            "output": ConnectorConfigAddActuatorConfigOutput,
        },
        "create_connector": {
            "canonical": {
                "name": "create_connector",
                "description": "Create one deterministic Connector instance under this Connector config.\n\nContract:\n- Config -> Instance is the canonical ownership rail.\n- Parent `ConnectorConfig` scope is propagated by constructor lowering.\n- `connector_instance_key` identifies this runtime fulfillment.",
                "is_constructor": False,
            },
            "input": ConnectorConfigCreateConnectorInput,
            "output": ConnectorConfigCreateConnectorOutput,
        },
    },
}

__all__ = [
    "ConnectorConfig",
    "ConnectorConfigCreateInput",
    "ConnectorConfigCreateOutput",
    "ConnectorConfigAddProviderInput",
    "ConnectorConfigAddProviderOutput",
    "ConnectorConfigAddSensorConfigInput",
    "ConnectorConfigAddSensorConfigOutput",
    "ConnectorConfigAddActuatorConfigInput",
    "ConnectorConfigAddActuatorConfigOutput",
    "ConnectorConfigCreateConnectorInput",
    "ConnectorConfigCreateConnectorOutput",
    "FUNCTIONS",
]
