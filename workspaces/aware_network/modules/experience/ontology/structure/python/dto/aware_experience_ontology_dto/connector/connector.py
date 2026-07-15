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
    from aware_experience_ontology_dto.sensor.sensor import Sensor


class Connector(BaseModel):
    """
    Connector instance.
    Contract:
    - A Connector instance is an actual runtime fulfillment of a Connector config.
    - It links to the Sensor and Actuator instances fulfilled by the same connector.
    - Runtime refs are adapter hints; provenance receipts are added in later
    invocation-action bridge slices.
    """

    # Relationships
    sensors: list[Sensor] = Field(default_factory=list)
    actuators: list[Actuator] = Field(default_factory=list)

    # Attributes
    connector_instance_key: str
    runtime_ref: str | None = Field(default=None)
    status: str = Field(default="active")
