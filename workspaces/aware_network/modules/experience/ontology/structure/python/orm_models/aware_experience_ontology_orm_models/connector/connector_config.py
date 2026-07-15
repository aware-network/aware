from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.actuator.actuator_config import ActuatorConfig
    from aware_experience_ontology_orm_models.connector.connector import Connector
    from aware_experience_ontology_orm_models.connector.connector_provider import ConnectorProvider
    from aware_experience_ontology_orm_models.sensor.sensor_config import SensorConfig


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
