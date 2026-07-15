from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.actuator.actuator import Actuator
    from aware_experience_ontology_orm_models.actuator.actuator_config_state_node import ActuatorConfigStateNode
    from aware_experience_ontology_orm_models.actuator.actuator_invocation_action_config import (
        ActuatorInvocationActionConfig,
    )


class ActuatorConfig(ORMModel):
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

    # Foreign Keys
    connector_config_id: UUID = Field(description="Foreign key for ConnectorConfig.actuator_configs")
