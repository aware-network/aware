from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.actuator.actuator import Actuator
    from aware_experience_ontology_dto.actuator.actuator_config_state_node import ActuatorConfigStateNode
    from aware_experience_ontology_dto.actuator.actuator_invocation_action_config import ActuatorInvocationActionConfig


class ActuatorConfig(BaseModel):
    """
    Actuator configuration.
    Contract:
    - An Actuator config describes outbound action capability a Connector can perform.
    - Actuator instances are runtime fulfillments declared under this config.
    - Affected state-node footprint declares which Projection nodes this
    actuator can affect; payload DTOs are resolved only through invocation
    bindings.
    - Invocation action config bindings expose the shared Experience invocation
    target surface without duplicating API/SDK/service fields.
    """

    # Relationships
    invocation_action_configs: list[ActuatorInvocationActionConfig] = Field(default_factory=list)
    affected_state_nodes: list[ActuatorConfigStateNode] = Field(default_factory=list)
    actuators: list[Actuator] = Field(default_factory=list)

    # Attributes
    actuator_key: str
    actuator_kind: str
    target_ref: str | None = Field(default=None)
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
