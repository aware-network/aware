from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.actuator.actuator_config import ActuatorConfig
    from aware_experience_ontology_dto.connector.connector import Connector
    from aware_experience_ontology_dto.connector.connector_provider import ConnectorProvider
    from aware_experience_ontology_dto.sensor.sensor_config import SensorConfig


class ConnectorConfig(BaseModel):
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
