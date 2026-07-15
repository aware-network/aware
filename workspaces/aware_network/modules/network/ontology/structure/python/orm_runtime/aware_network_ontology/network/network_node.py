from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology
from aware_network_ontology.network.network_enums import (
    NetworkEnvironmentRole,
    NetworkNodeStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_identity_ontology.actor.actor import Actor
    from aware_network_ontology.network.network_node_config import NetworkNodeConfig
    from aware_network_ontology.network.network_node_environment import NetworkNodeEnvironment
    from aware_network_ontology.network.network_node_member import NetworkNodeMember
    from aware_network_ontology.network.network_node_service import NetworkNodeService


class NetworkNode(ORMModel):
    # Relationships
    config: NetworkNodeConfig | None = Field(default=None, exclude=True)
    environments: list[NetworkNodeEnvironment] = Field(default_factory=list)
    members: list[NetworkNodeMember] = Field(default_factory=list, exclude=True)
    services: list[NetworkNodeService] = Field(default_factory=list)
    system_actor: Actor | None = Field(
        default=None,
        description="Node-owned system Actor used for bootstrap and topology-publication provenance.\nContract:\n- Node bootstrap/self-registration is never actorless.\n- The Node system Actor is stable before human/operator or commercial\ncontract admission exists.\n- Future contract-gated registration still uses this Node Actor as the\nprovenance subject; commercial terms add a gate, not an actorless path.",
    )

    # Attributes
    base_url: str | None = Field(default=None)
    hostname: str
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    port: int
    public_key: str
    status: NetworkNodeStatus = Field(default=NetworkNodeStatus.inactive)

    # Foreign Keys
    config_id: UUID | None = Field(default=None, description="Foreign key for NetworkNode.config")
    system_actor_id: UUID | None = Field(default=None, description="Foreign key for NetworkNode.system_actor")

    @classmethod
    async def register(
        cls,
        public_key: str,
        hostname: str,
        port: int,
        base_url: str | None = None,
        node_id: UUID | None = None,
        system_actor_id: UUID | None = None,
        status: NetworkNodeStatus = NetworkNodeStatus.active,
    ) -> NetworkNode:
        """
        Registers (or updates) a NetworkNode by its public key.

        Contract:
        - `public_key` is the canonical identity key for NetworkNode.
        - `node_id` may be supplied by a running Node runtime when that runtime
          already owns a canonical local node identity. In that case the
          committed NetworkNode id must match the runtime node id used for
          peer and route resolution.
        - `system_actor_id` links the registered NetworkNode to the Node-owned
          system Actor that emitted the self-registration.
        - Idempotent: repeated calls yield the same NetworkNode.id for the same anchor.
        """

        payload = {
            "public_key": public_key,
            "hostname": hostname,
            "port": port,
            "base_url": base_url,
            "node_id": node_id,
            "system_actor_id": system_actor_id,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="register", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NetworkNode):
            return value
        return NetworkNode.validate_invocation_value(value)

    async def upsert_environment(
        self,
        environment_id: UUID,
        role: NetworkEnvironmentRole = NetworkEnvironmentRole.replica,
        is_active: bool = True,
        priority: int = 0,
    ) -> NetworkNode:
        """
        Upsert an environment association for this node (v0).

        Contract:
        - Idempotent by (node.id, environment_id).
        - Environment is referenced via portal (no embedded Environment objects in-lane).
        """

        payload = {"environment_id": environment_id, "role": role, "is_active": is_active, "priority": priority}
        result = await invoke_instance(orm_model=self, function_name="upsert_environment", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NetworkNode):
            return value
        return NetworkNode.validate_invocation_value(value)

    async def attach_service(
        self,
        service_package_id: UUID,
        service_id: UUID,
        host_id: str,
        protocol_version: str,
        service_name: str,
        endpoint_refs: list[str] = [],
        stream_endpoint_refs: list[str] = [],
        host_version: str | None = None,
        supports_stream_events: bool = False,
    ) -> NetworkNodeService:
        """
        Attach one Node-owned hosted-Service advertisement binding (v0).

        Contract:
        - Idempotent by (node.id, service_package_id).
        - This is live network discovery truth for one hosted Service, not desired deploy-state
          truth from `NodeConfig`.
        - The target `Service` is referenced via a real portal so later consumers can resolve the
          semantic service contract. The target `ServicePackage` is referenced via a real portal
          so remote Service API dependency resolution joins against Service-owned package truth.
        """

        payload = {
            "service_package_id": service_package_id,
            "service_id": service_id,
            "host_id": host_id,
            "protocol_version": protocol_version,
            "service_name": service_name,
            "endpoint_refs": endpoint_refs,
            "stream_endpoint_refs": stream_endpoint_refs,
            "host_version": host_version,
            "supports_stream_events": supports_stream_events,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_service", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_network_ontology.network.network_node_service import NetworkNodeService

        if isinstance(value, NetworkNodeService):
            return value
        return NetworkNodeService.validate_invocation_value(value)


class NetworkNodeRegisterInput(BaseModel):
    public_key: str
    hostname: str
    port: int
    base_url: str | None = Field(default=None)
    node_id: UUID | None = Field(default=None)
    system_actor_id: UUID | None = Field(default=None)
    status: NetworkNodeStatus = Field(default=NetworkNodeStatus.active)


class NetworkNodeRegisterOutput(BaseModel):
    value: NetworkNode


class NetworkNodeUpsertEnvironmentInput(BaseModel):
    environment_id: UUID
    role: NetworkEnvironmentRole = Field(default=NetworkEnvironmentRole.replica)
    is_active: bool = Field(default=True)
    priority: int = Field(default=0)


class NetworkNodeUpsertEnvironmentOutput(BaseModel):
    value: NetworkNode


class NetworkNodeAttachServiceInput(BaseModel):
    service_package_id: UUID
    service_id: UUID
    host_id: str
    protocol_version: str
    service_name: str
    endpoint_refs: list[str] = Field(default_factory=list)
    stream_endpoint_refs: list[str] = Field(default_factory=list)
    host_version: str | None = Field(default=None)
    supports_stream_events: bool = Field(default=False)


class NetworkNodeAttachServiceOutput(BaseModel):
    value: NetworkNodeService


FUNCTIONS = {
    "NetworkNode": {
        "register": {
            "canonical": {
                "name": "register",
                "description": "Registers (or updates) a NetworkNode by its public key.\n\nContract:\n- `public_key` is the canonical identity key for NetworkNode.\n- `node_id` may be supplied by a running Node runtime when that runtime\n  already owns a canonical local node identity. In that case the\n  committed NetworkNode id must match the runtime node id used for\n  peer and route resolution.\n- `system_actor_id` links the registered NetworkNode to the Node-owned\n  system Actor that emitted the self-registration.\n- Idempotent: repeated calls yield the same NetworkNode.id for the same anchor.",
                "is_constructor": True,
            },
            "input": NetworkNodeRegisterInput,
            "output": NetworkNodeRegisterOutput,
        },
        "upsert_environment": {
            "canonical": {
                "name": "upsert_environment",
                "description": "Upsert an environment association for this node (v0).\n\nContract:\n- Idempotent by (node.id, environment_id).\n- Environment is referenced via portal (no embedded Environment objects in-lane).",
                "is_constructor": False,
            },
            "input": NetworkNodeUpsertEnvironmentInput,
            "output": NetworkNodeUpsertEnvironmentOutput,
        },
        "attach_service": {
            "canonical": {
                "name": "attach_service",
                "description": "Attach one Node-owned hosted-Service advertisement binding (v0).\n\nContract:\n- Idempotent by (node.id, service_package_id).\n- This is live network discovery truth for one hosted Service, not desired deploy-state\n  truth from `NodeConfig`.\n- The target `Service` is referenced via a real portal so later consumers can resolve the\n  semantic service contract. The target `ServicePackage` is referenced via a real portal\n  so remote Service API dependency resolution joins against Service-owned package truth.",
                "is_constructor": False,
            },
            "input": NetworkNodeAttachServiceInput,
            "output": NetworkNodeAttachServiceOutput,
        },
    },
}

__all__ = [
    "NetworkNode",
    "NetworkNodeRegisterInput",
    "NetworkNodeRegisterOutput",
    "NetworkNodeUpsertEnvironmentInput",
    "NetworkNodeUpsertEnvironmentOutput",
    "NetworkNodeAttachServiceInput",
    "NetworkNodeAttachServiceOutput",
    "FUNCTIONS",
]
