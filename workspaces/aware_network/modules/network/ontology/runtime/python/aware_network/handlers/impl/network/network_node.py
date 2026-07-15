from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Network Ontology
from aware_network_ontology.network.network_enums import (
    NetworkEnvironmentRole,
    NetworkNodeStatus,
)
from aware_network_ontology.network.network_node import NetworkNode
from aware_network_ontology.network.network_node_service import NetworkNodeService

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Identity Runtime
from aware_identity.auth.public_key.generator import canonicalize_ed25519_public_key

# Network Ontology
from aware_network_ontology.network.network_node_environment import (
    NetworkNodeEnvironment,
)

from aware_network_ontology.stable_ids import (
    stable_network_node_environment_id,
    stable_network_node_id,
    stable_network_node_service_id,
)

# --- AWARE: USER_IMPORTS END


async def register(
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

    # --- AWARE: LOGIC START register
    try:
        canonical_key, _key_bytes = canonicalize_ed25519_public_key(public_key)
    except Exception:
        canonical_key = public_key
    resolved_node_id = stable_network_node_id(public_key=public_key)
    if node_id is not None and node_id != resolved_node_id:
        raise ValueError(
            "NetworkNode.register node_id must match the public_key semantic identity "
            f"(node_id={node_id} semantic_node_id={resolved_node_id})."
        )
    return NetworkNode(
        id=resolved_node_id,
        public_key=canonical_key,
        base_url=base_url,
        hostname=hostname,
        port=port,
        status=status,
        system_actor_id=system_actor_id,
    )
    # --- AWARE: LOGIC END register


async def upsert_environment(
    network_node: NetworkNode,
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

    # --- AWARE: LOGIC START upsert_environment
    expected_id = stable_network_node_environment_id(
        network_node_id=network_node.id,
        environment_id=environment_id,
    )

    existing: NetworkNodeEnvironment | None = None
    for assoc in list(network_node.environments or []):
        if getattr(assoc, "id", None) == expected_id:
            existing = assoc
            break
        if getattr(assoc, "environment_id", None) == environment_id:
            existing = assoc
            break

    if existing is None:
        assoc = await NetworkNodeEnvironment.create_via_network_node(
            network_node_id=network_node.id,
            environment_id=environment_id,
            role=role,
            is_active=is_active,
            priority=priority,
        )
        network_node.environments.append(assoc)
        return network_node

    return network_node
    # --- AWARE: LOGIC END upsert_environment


async def attach_service(
    network_node: NetworkNode,
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

    # --- AWARE: LOGIC START attach_service
    expected_id = stable_network_node_service_id(
        network_node_id=network_node.id,
        service_package_id=service_package_id,
    )

    existing: NetworkNodeService | None = None
    for binding in list(network_node.services or []):
        if getattr(binding, "id", None) == expected_id:
            existing = binding
            break
        if getattr(binding, "service_package_id", None) == service_package_id:
            existing = binding
            break

    if existing is None:
        binding = await NetworkNodeService.build_via_network_node(
            network_node_id=network_node.id,
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
        network_node.services.append(binding)
        return binding

    return existing
    # --- AWARE: LOGIC END attach_service
