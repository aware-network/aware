from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.sensor.sensor import Sensor
    from aware_experience_ontology_orm_models.sensor.sensor_config_state_node import SensorConfigStateNode
    from aware_experience_ontology_orm_models.sensor.sensor_invocation_action_config import SensorInvocationActionConfig


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
