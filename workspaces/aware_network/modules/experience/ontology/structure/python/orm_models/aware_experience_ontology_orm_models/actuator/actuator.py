from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.actuator.actuator_invocation_action import ActuatorInvocationAction


class Actuator(ORMModel):
    """
    Actuator instance.
    Contract:
    - An Actuator instance is a runtime fulfillment of an Actuator config.
    - It links concrete invocations to the shared Experience invocation spine.
    """

    # Relationships
    invocation_actions: list[ActuatorInvocationAction] = Field(default_factory=list)

    # Attributes
    actuator_instance_key: str
    external_ref: str | None = Field(default=None)
    status: str = Field(default="active")

    # Foreign Keys
    actuator_config_id: UUID = Field(description="Foreign key for ActuatorConfig.actuators")
