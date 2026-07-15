from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Network Ontology
from aware_network_ontology.network.network_node_service import NetworkNodeService

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Network Ontology
from aware_network_ontology.stable_ids import stable_network_node_service_id

# --- AWARE: USER_IMPORTS END


async def build_via_network_node(
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

    # --- AWARE: LOGIC START build_via_network_node
    binding_id = stable_network_node_service_id(
        network_node_id=network_node_id,
        service_package_id=service_package_id,
    )

    return NetworkNodeService(
        id=binding_id,
        network_node_id=network_node_id,
        service_package_id=service_package_id,
        service_id=service_id,
        host_id=host_id,
        protocol_version=protocol_version,
        service_name=service_name,
        endpoint_refs=list(endpoint_refs),
        stream_endpoint_refs=list(stream_endpoint_refs),
        host_version=host_version,
        supports_stream_events=supports_stream_events,
    )
    # --- AWARE: LOGIC END build_via_network_node
