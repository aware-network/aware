from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.actuator.actuator_invocation_action import ActuatorInvocationAction


class Actuator(BaseModel):
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
