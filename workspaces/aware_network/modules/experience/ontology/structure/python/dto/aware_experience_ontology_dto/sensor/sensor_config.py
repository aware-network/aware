from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.sensor.sensor import Sensor
    from aware_experience_ontology_dto.sensor.sensor_config_state_node import SensorConfigStateNode
    from aware_experience_ontology_dto.sensor.sensor_invocation_action_config import SensorInvocationActionConfig


class SensorConfig(BaseModel):
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
