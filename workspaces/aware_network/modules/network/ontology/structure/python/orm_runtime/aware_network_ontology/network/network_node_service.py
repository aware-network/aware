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
    from aware_service_ontology.service.service import Service
    from aware_service_ontology.service.service_package import ServicePackage


class NetworkNodeService(ORMModel):
    # Relationships
    service: Service | None = Field(default=None)
    service_package: ServicePackage | None = Field(default=None)

    # Attributes
    endpoint_refs: list[str] = Field(default_factory=list)
    host_id: str
    host_version: str | None = Field(default=None)
    protocol_version: str
    service_name: str
    stream_endpoint_refs: list[str] = Field(default_factory=list)
    supports_stream_events: bool = Field(default=False)

    # Foreign Keys
    network_node_id: UUID = Field(description="Foreign key for NetworkNode.services")
    service_id: UUID = Field(description="Foreign key for NetworkNodeService.service")
    service_package_id: UUID = Field(description="Foreign key for NetworkNodeService.service_package")

    @classmethod
    async def build_via_network_node(
        cls,
        network_node_id: UUID,
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
        Create one NetworkNode↔Service hosted-service advertisement binding (v0).

        Contract:
        - Deterministic id by (network_node_id, service_package_id) where `network_node_id` is
          parent-propagated.
        - Lives in the `network_node` lane as Node-owned hosted-service discovery truth.
        - Binds to a real `Service` portal so Network discovery resolves semantic service truth
          relationally.
        - Binds to a real `ServicePackage` portal because ServicePackage is the dependency unit
          used by Service API provider resolution.
        - `service_name` is the advertised route key committed by the hosting node for
          discovery/read-model indexing; the semantic service identity remains the `service`
          portal.
        - Live readiness/liveness status remains a separate control-plane rail.
        """

        payload = {
            "network_node_id": network_node_id,
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
        result = await invoke_constructor(orm_class=cls, function_name="build_via_network_node", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NetworkNodeService):
            return value
        return NetworkNodeService.validate_invocation_value(value)


class NetworkNodeServiceBuildViaNetworkNodeInput(BaseModel):
    network_node_id: UUID = Field(description="Foreign key for NetworkNode.services")
    service_package_id: UUID
    service_id: UUID
    host_id: str
    protocol_version: str
    service_name: str
    endpoint_refs: list[str] = Field(default_factory=list)
    stream_endpoint_refs: list[str] = Field(default_factory=list)
    host_version: str | None = Field(default=None)
    supports_stream_events: bool = Field(default=False)


class NetworkNodeServiceBuildViaNetworkNodeOutput(BaseModel):
    value: NetworkNodeService


FUNCTIONS = {
    "NetworkNodeService": {
        "build_via_network_node": {
            "canonical": {
                "name": "build_via_network_node",
                "description": "Create one NetworkNode↔Service hosted-service advertisement binding (v0).\n\nContract:\n- Deterministic id by (network_node_id, service_package_id) where `network_node_id` is\n  parent-propagated.\n- Lives in the `network_node` lane as Node-owned hosted-service discovery truth.\n- Binds to a real `Service` portal so Network discovery resolves semantic service truth\n  relationally.\n- Binds to a real `ServicePackage` portal because ServicePackage is the dependency unit\n  used by Service API provider resolution.\n- `service_name` is the advertised route key committed by the hosting node for\n  discovery/read-model indexing; the semantic service identity remains the `service`\n  portal.\n- Live readiness/liveness status remains a separate control-plane rail.",
                "is_constructor": True,
            },
            "input": NetworkNodeServiceBuildViaNetworkNodeInput,
            "output": NetworkNodeServiceBuildViaNetworkNodeOutput,
        },
    },
}

__all__ = [
    "NetworkNodeService",
    "NetworkNodeServiceBuildViaNetworkNodeInput",
    "NetworkNodeServiceBuildViaNetworkNodeOutput",
    "FUNCTIONS",
]
