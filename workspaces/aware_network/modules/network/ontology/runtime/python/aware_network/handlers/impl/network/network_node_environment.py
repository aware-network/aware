from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Network Ontology
from aware_network_ontology.network.network_enums import NetworkEnvironmentRole
from aware_network_ontology.network.network_node_environment import NetworkNodeEnvironment

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Network Ontology
from aware_network_ontology.stable_ids import stable_network_node_environment_id

# --- AWARE: USER_IMPORTS END


async def create_via_network_node(
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

    # --- AWARE: LOGIC START create_via_network_node
    assoc_id = stable_network_node_environment_id(
        network_node_id=network_node_id,
        environment_id=environment_id,
    )

    return NetworkNodeEnvironment(
        id=assoc_id,
        network_node_id=network_node_id,
        environment_id=environment_id,
        role=role,
        is_active=is_active,
        priority=priority,
    )
    # --- AWARE: LOGIC END create_via_network_node
