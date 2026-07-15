from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Network Ontology
from aware_network_ontology.network.network_enums import NetworkFanoutMode
from aware_network_ontology.network.network_node_peer_fanout_rule import NetworkNodePeerFanoutRule

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Network Ontology
from aware_network_ontology.stable_ids import stable_network_node_peer_fanout_rule_id

# --- AWARE: USER_IMPORTS END


async def create_via_network_node_peer(
    network_node_peer_id: UUID,
    lane_branch_id: UUID,
    lane_projection_hash: str,
    enabled: bool = True,
    mode: NetworkFanoutMode = NetworkFanoutMode.notify_pull,
) -> NetworkNodePeerFanoutRule:
    """
    Create a peer fan-out rule (v0).

    Contract:
    - Deterministic id by (network_node_peer_id, lane key) where `network_node_peer_id` is
    parent-propagated.
    - Requires invocation branch_id to match network_node_peer_id (rule lives in the peer lane).
    """

    # --- AWARE: LOGIC START create_via_network_node_peer
    lane_projection_hash = (lane_projection_hash or "").strip()
    if not lane_projection_hash:
        raise ValueError("lane_projection_hash is required")

    rule_id = stable_network_node_peer_fanout_rule_id(
        network_node_peer_id=network_node_peer_id,
        lane_branch_id=lane_branch_id,
        lane_projection_hash=lane_projection_hash,
    )

    return NetworkNodePeerFanoutRule(
        id=rule_id,
        network_node_peer_id=network_node_peer_id,
        lane_branch_id=lane_branch_id,
        lane_projection_hash=lane_projection_hash,
        enabled=enabled,
        mode=mode,
    )
    # --- AWARE: LOGIC END create_via_network_node_peer
