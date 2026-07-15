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
    from aware_experience_ontology_orm_models.sensor.sensor import Sensor


class Connector(ORMModel):
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

    # Foreign Keys
    connector_config_id: UUID = Field(description="Foreign key for ConnectorConfig.connectors")
