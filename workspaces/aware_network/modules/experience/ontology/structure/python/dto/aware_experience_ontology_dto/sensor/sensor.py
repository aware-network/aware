from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.sensor.sensor_invocation_action import SensorInvocationAction


class Sensor(BaseModel):
    """
    Sensor instance.
    Contract:
    - A Sensor instance is a runtime fulfillment of a Sensor config.
    - It links concrete invocations to the shared Experience invocation spine.
    """

    # Relationships
    invocation_actions: list[SensorInvocationAction] = Field(default_factory=list)

    # Attributes
    sensor_instance_key: str
    external_ref: str | None = Field(default=None)
    status: str = Field(default="active")
