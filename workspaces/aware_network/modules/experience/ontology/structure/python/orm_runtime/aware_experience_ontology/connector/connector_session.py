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
    from aware_experience_ontology.connector.connector import Connector


class ConnectorSession(ORMModel):
    """
    Connector provider session.
    Contract:
    - A ConnectorSession is the concrete provider/session fulfillment context.
    - It links a provider config to one runtime Connector instance.
    - Connector owns the fulfilled Sensor/Actuator instances and invocation
    receipts remain on the shared Experience invocation spine.
    """

    # Relationships
    connector: Connector | None = Field(default=None)

    # Attributes
    session_key: str
    session_ref: str | None = Field(default=None)
    host_ref: str | None = Field(default=None)
    principal_ref: str | None = Field(default=None)
    status: str = Field(default="active")

    # Foreign Keys
    connector_provider_id: UUID = Field(description="Foreign key for ConnectorProvider.sessions")
    connector_id: UUID = Field(description="Foreign key for ConnectorSession.connector")

    @classmethod
    async def build_via_connector_provider(
        cls,
        connector_provider_id: UUID,
        connector_id: UUID,
        session_key: str,
        session_ref: str | None = None,
        host_ref: str | None = None,
        principal_ref: str | None = None,
        status: str = "active",
    ) -> ConnectorSession:
        """
        Create one deterministic Connector session under a ConnectorProvider.

        Contract:
        - Parent `ConnectorProvider` scope is propagated by constructor lowering.
        - `connector_id` binds the session to the runtime Connector fulfillment.
        - `session_key` identifies the concrete provider session.
        """

        payload = {
            "connector_provider_id": connector_provider_id,
            "connector_id": connector_id,
            "session_key": session_key,
            "session_ref": session_ref,
            "host_ref": host_ref,
            "principal_ref": principal_ref,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_connector_provider", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ConnectorSession):
            return value
        return ConnectorSession.validate_invocation_value(value)


class ConnectorSessionBuildViaConnectorProviderInput(BaseModel):
    connector_provider_id: UUID = Field(description="Foreign key for ConnectorProvider.sessions")
    connector_id: UUID
    session_key: str
    session_ref: str | None = Field(default=None)
    host_ref: str | None = Field(default=None)
    principal_ref: str | None = Field(default=None)
    status: str = Field(default="active")


class ConnectorSessionBuildViaConnectorProviderOutput(BaseModel):
    value: ConnectorSession


FUNCTIONS = {
    "ConnectorSession": {
        "build_via_connector_provider": {
            "canonical": {
                "name": "build_via_connector_provider",
                "description": "Create one deterministic Connector session under a ConnectorProvider.\n\nContract:\n- Parent `ConnectorProvider` scope is propagated by constructor lowering.\n- `connector_id` binds the session to the runtime Connector fulfillment.\n- `session_key` identifies the concrete provider session.",
                "is_constructor": True,
            },
            "input": ConnectorSessionBuildViaConnectorProviderInput,
            "output": ConnectorSessionBuildViaConnectorProviderOutput,
        },
    },
}

__all__ = [
    "ConnectorSession",
    "ConnectorSessionBuildViaConnectorProviderInput",
    "ConnectorSessionBuildViaConnectorProviderOutput",
    "FUNCTIONS",
]
