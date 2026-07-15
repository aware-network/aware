from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology
from aware_network_ontology.network.network_enums import NetworkEnvironmentRole

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_environment_ontology.environment.environment import Environment


class NetworkNodeEnvironment(ORMModel):
    # Relationships
    environment: Environment | None = Field(default=None, exclude=True)

    # Attributes
    is_active: bool = Field(default=True)
    priority: int = Field(default=0)
    role: NetworkEnvironmentRole = Field(default=NetworkEnvironmentRole.replica)

    # Foreign Keys
    network_node_id: UUID = Field(description="Foreign key for NetworkNode.environments")
    environment_id: UUID = Field(description="Foreign key for NetworkNodeEnvironment.environment")

    @classmethod
    async def create_via_network_node(
        cls,
        network_node_id: UUID,
        environment_id: UUID,
        role: NetworkEnvironmentRole = NetworkEnvironmentRole.replica,
        is_active: bool = True,
        priority: int = 0,
    ) -> NetworkNodeEnvironment:
        """
        Create a Node↔Environment association (v0).

        Contract:
        - Deterministic id by (network_node_id, environment_id) where `network_node_id` is
        parent-propagated.
        - Requires invocation branch_id to match network_node_id (assoc lives in the node lane).
        - Environment config, key/title, and experience profiles are resolved through
          the `environment` portal; Network must not copy them as second truth.
        """

        payload = {
            "network_node_id": network_node_id,
            "environment_id": environment_id,
            "role": role,
            "is_active": is_active,
            "priority": priority,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_network_node", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NetworkNodeEnvironment):
            return value
        return NetworkNodeEnvironment.validate_invocation_value(value)


class NetworkNodeEnvironmentCreateViaNetworkNodeInput(BaseModel):
    network_node_id: UUID = Field(description="Foreign key for NetworkNode.environments")
    environment_id: UUID
    role: NetworkEnvironmentRole = Field(default=NetworkEnvironmentRole.replica)
    is_active: bool = Field(default=True)
    priority: int = Field(default=0)


class NetworkNodeEnvironmentCreateViaNetworkNodeOutput(BaseModel):
    value: NetworkNodeEnvironment


FUNCTIONS = {
    "NetworkNodeEnvironment": {
        "create_via_network_node": {
            "canonical": {
                "name": "create_via_network_node",
                "description": "Create a Node↔Environment association (v0).\n\nContract:\n- Deterministic id by (network_node_id, environment_id) where `network_node_id` is parent-propagated.\n- Requires invocation branch_id to match network_node_id (assoc lives in the node lane).\n- Environment config, key/title, and experience profiles are resolved through\n  the `environment` portal; Network must not copy them as second truth.",
                "is_constructor": True,
            },
            "input": NetworkNodeEnvironmentCreateViaNetworkNodeInput,
            "output": NetworkNodeEnvironmentCreateViaNetworkNodeOutput,
        },
    },
}

__all__ = [
    "NetworkNodeEnvironment",
    "NetworkNodeEnvironmentCreateViaNetworkNodeInput",
    "NetworkNodeEnvironmentCreateViaNetworkNodeOutput",
    "FUNCTIONS",
]
