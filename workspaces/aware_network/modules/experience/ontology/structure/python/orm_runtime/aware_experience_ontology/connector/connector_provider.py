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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_experience_ontology.connector.connector_session import ConnectorSession


class ConnectorProvider(ORMModel):
    """
    Connector provider configuration.
    Contract:
    - A ConnectorProvider identifies a concrete provider for a ConnectorConfig
    capability family.
    - Provider config is reusable and does not represent a live login/session.
    - ConnectorSession records concrete provider fulfillment context and links
    to the runtime Connector instance.
    """

    # Relationships
    sessions: list[ConnectorSession] = Field(default_factory=list)

    # Attributes
    provider_key: str
    provider_kind: str
    provider_ref: str | None = Field(default=None)
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    connector_config_id: UUID = Field(description="Foreign key for ConnectorConfig.providers")

    async def create_session(
        self,
        connector_id: UUID,
        session_key: str,
        session_ref: str | None = None,
        host_ref: str | None = None,
        principal_ref: str | None = None,
        status: str = "active",
    ) -> ConnectorSession:
        """
        Create one concrete provider session bound to a Connector instance.

        Contract:
        - Provider config stays reusable.
        - Session identity captures the concrete fulfillment context, e.g.
          a YouTube Music session on the FutureHills clinic computer.
        - The linked Connector owns fulfilled Sensor/Actuator instances.
        """

        payload = {
            "connector_id": connector_id,
            "session_key": session_key,
            "session_ref": session_ref,
            "host_ref": host_ref,
            "principal_ref": principal_ref,
            "status": status,
        }
        result = await invoke_instance(orm_model=self, function_name="create_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.connector.connector_session import ConnectorSession

        if isinstance(value, ConnectorSession):
            return value
        return ConnectorSession.validate_invocation_value(value)

    @classmethod
    async def build_via_connector_config(
        cls,
        connector_config_id: UUID,
        provider_key: str,
        provider_kind: str,
        provider_ref: str | None = None,
        label: str | None = None,
        description: str | None = None,
    ) -> ConnectorProvider:
        """
        Create one deterministic provider config under a ConnectorConfig.

        Contract:
        - Parent `ConnectorConfig` scope is propagated by constructor lowering.
        - `provider_key` is stable within the Connector config.
        - `provider_kind` identifies the concrete external provider.
        """

        payload = {
            "connector_config_id": connector_config_id,
            "provider_key": provider_key,
            "provider_kind": provider_kind,
            "provider_ref": provider_ref,
            "label": label,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_connector_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ConnectorProvider):
            return value
        return ConnectorProvider.validate_invocation_value(value)


class ConnectorProviderCreateSessionInput(BaseModel):
    connector_id: UUID
    session_key: str
    session_ref: str | None = Field(default=None)
    host_ref: str | None = Field(default=None)
    principal_ref: str | None = Field(default=None)
    status: str = Field(default="active")


class ConnectorProviderCreateSessionOutput(BaseModel):
    value: ConnectorSession


class ConnectorProviderBuildViaConnectorConfigInput(BaseModel):
    connector_config_id: UUID = Field(description="Foreign key for ConnectorConfig.providers")
    provider_key: str
    provider_kind: str
    provider_ref: str | None = Field(default=None)
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ConnectorProviderBuildViaConnectorConfigOutput(BaseModel):
    value: ConnectorProvider


FUNCTIONS = {
    "ConnectorProvider": {
        "create_session": {
            "canonical": {
                "name": "create_session",
                "description": "Create one concrete provider session bound to a Connector instance.\n\nContract:\n- Provider config stays reusable.\n- Session identity captures the concrete fulfillment context, e.g.\n  a YouTube Music session on the FutureHills clinic computer.\n- The linked Connector owns fulfilled Sensor/Actuator instances.",
                "is_constructor": False,
            },
            "input": ConnectorProviderCreateSessionInput,
            "output": ConnectorProviderCreateSessionOutput,
        },
        "build_via_connector_config": {
            "canonical": {
                "name": "build_via_connector_config",
                "description": "Create one deterministic provider config under a ConnectorConfig.\n\nContract:\n- Parent `ConnectorConfig` scope is propagated by constructor lowering.\n- `provider_key` is stable within the Connector config.\n- `provider_kind` identifies the concrete external provider.",
                "is_constructor": True,
            },
            "input": ConnectorProviderBuildViaConnectorConfigInput,
            "output": ConnectorProviderBuildViaConnectorConfigOutput,
        },
    },
}

__all__ = [
    "ConnectorProvider",
    "ConnectorProviderCreateSessionInput",
    "ConnectorProviderCreateSessionOutput",
    "ConnectorProviderBuildViaConnectorConfigInput",
    "ConnectorProviderBuildViaConnectorConfigOutput",
    "FUNCTIONS",
]
