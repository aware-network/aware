from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_experience_ontology.actuator.actuator import Actuator
    from aware_experience_ontology.sensor.sensor import Sensor


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

    @classmethod
    async def build_via_connector_config(
        cls,
        connector_config_id: UUID,
        connector_instance_key: str,
        runtime_ref: str | None = None,
        status: str = "active",
    ) -> Connector:
        """
        Create one deterministic Connector instance under a ConnectorConfig.

        Contract:
        - Parent `ConnectorConfig` scope is propagated by constructor lowering.
        - `connector_instance_key` identifies this runtime fulfillment.
        """

        payload = {
            "connector_config_id": connector_config_id,
            "connector_instance_key": connector_instance_key,
            "runtime_ref": runtime_ref,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_connector_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Connector):
            return value
        return Connector.validate_invocation_value(value)


class ConnectorBuildViaConnectorConfigInput(BaseModel):
    connector_config_id: UUID = Field(description="Foreign key for ConnectorConfig.connectors")
    connector_instance_key: str
    runtime_ref: str | None = Field(default=None)
    status: str = Field(default="active")


class ConnectorBuildViaConnectorConfigOutput(BaseModel):
    value: Connector


FUNCTIONS = {
    "Connector": {
        "build_via_connector_config": {
            "canonical": {
                "name": "build_via_connector_config",
                "description": "Create one deterministic Connector instance under a ConnectorConfig.\n\nContract:\n- Parent `ConnectorConfig` scope is propagated by constructor lowering.\n- `connector_instance_key` identifies this runtime fulfillment.",
                "is_constructor": True,
            },
            "input": ConnectorBuildViaConnectorConfigInput,
            "output": ConnectorBuildViaConnectorConfigOutput,
        },
    },
}

__all__ = [
    "Connector",
    "ConnectorBuildViaConnectorConfigInput",
    "ConnectorBuildViaConnectorConfigOutput",
    "FUNCTIONS",
]
