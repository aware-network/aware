from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Network Ontology
from aware_network_ontology.network.network_enums import (
    NetworkFanoutMode,
    NetworkRequestStatus,
)
from aware_network_ontology.network.network_node_peer import NetworkNodePeer

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Network Ontology
from aware_network_ontology.network.network_node_peer_fanout_rule import (
    NetworkNodePeerFanoutRule,
)

# Network Ontology
from aware_network_ontology.stable_ids import (
    stable_network_node_peer_fanout_rule_id,
    stable_network_node_peer_id,
)

# --- AWARE: USER_IMPORTS END


async def create(network_node_id: UUID, peer_node_id: UUID, peer_http_base_url: str | None = None) -> NetworkNodePeer:
    """
    Creates an accepted peer link between two NetworkNodes (v0 bootstrap).

    Contract:
    - Deterministic NetworkNodePeer.id (stable by (network_node_id, peer_node_id)).
    - Idempotent: repeated calls yield the same NetworkNodePeer.id.
    - Sets status=`accepted`.
    """

    # --- AWARE: LOGIC START create
    peer_id = stable_network_node_peer_id(
        source_peer_node_id=network_node_id,
        target_peer_node_id=peer_node_id,
    )
    return NetworkNodePeer(
        id=peer_id,
        source_peer_node_id=network_node_id,
        target_peer_node_id=peer_node_id,
        status=NetworkRequestStatus.accepted,
        peer_http_base_url=peer_http_base_url,
    )
    # --- AWARE: LOGIC END create


async def request(network_node_id: UUID, peer_node_id: UUID, peer_http_base_url: str | None = None) -> NetworkNodePeer:
    """
    Creates a pending peer request between two NetworkNodes (v0).

    Contract:
    - Deterministic NetworkNodePeer.id (stable by (network_node_id, peer_node_id)).
    - Idempotent: repeated calls yield the same NetworkNodePeer.id.
    - Sets status=`pending`.
    """

    # --- AWARE: LOGIC START request
    peer_id = stable_network_node_peer_id(
        source_peer_node_id=network_node_id,
        target_peer_node_id=peer_node_id,
    )
    return NetworkNodePeer(
        id=peer_id,
        source_peer_node_id=network_node_id,
        target_peer_node_id=peer_node_id,
        status=NetworkRequestStatus.pending,
        peer_http_base_url=peer_http_base_url,
    )
    # --- AWARE: LOGIC END request


async def respond(network_node_peer: NetworkNodePeer, status: NetworkRequestStatus) -> NetworkNodePeer:
    """
    Accept or reject a pending NetworkNodePeer request (v0).

    Canonical contract:
    - Allowed transitions: pending -> accepted|rejected (idempotent).
    """

    # --- AWARE: LOGIC START respond
    if status not in (NetworkRequestStatus.accepted, NetworkRequestStatus.rejected):
        raise ValueError(f"Invalid peer response status: {status}. Allowed: accepted|rejected.")

    current = network_node_peer.status
    if current == status:
        return network_node_peer

    if current != NetworkRequestStatus.pending:
        raise ValueError(
            "Invalid peer status transition: " f"{current} -> {status} (only pending -> accepted|rejected allowed)."
        )

    network_node_peer.status = status
    return network_node_peer
    # --- AWARE: LOGIC END respond


async def upsert_fanout_rule(
    network_node_peer: NetworkNodePeer,
    lane_branch_id: UUID,
    lane_projection_hash: str,
    enabled: bool = True,
    mode: NetworkFanoutMode = NetworkFanoutMode.notify_pull,
) -> NetworkNodePeer:
    """
    Upsert a fan-out rule for this peer (v0).

    Contract:
    - Targets a lane key (`lane_branch_id`, `lane_projection_hash`).
    - Idempotent by (peer.id, lane key).
    """

    # --- AWARE: LOGIC START upsert_fanout_rule
    lane_projection_hash = (lane_projection_hash or "").strip()
    if not lane_projection_hash:
        raise ValueError("lane_projection_hash is required")

    expected_id = stable_network_node_peer_fanout_rule_id(
        network_node_peer_id=network_node_peer.id,
        lane_branch_id=lane_branch_id,
        lane_projection_hash=lane_projection_hash,
    )

    # Prefer stable-id match, fall back to lane-key match for back-compat.
    existing: NetworkNodePeerFanoutRule | None = None
    for rule in list(network_node_peer.fanout_rules or []):
        if getattr(rule, "id", None) == expected_id:
            existing = rule
            break
        if (
            getattr(rule, "lane_branch_id", None) == lane_branch_id
            and (getattr(rule, "lane_projection_hash", "") or "").strip() == lane_projection_hash
        ):
            existing = rule
            break

    if existing is None:
        rule = await NetworkNodePeerFanoutRule.create_via_network_node_peer(
            network_node_peer_id=network_node_peer.id,
            lane_branch_id=lane_branch_id,
            lane_projection_hash=lane_projection_hash,
            enabled=enabled,
            mode=mode,
        )
        network_node_peer.fanout_rules.append(rule)
        return network_node_peer

    changed = False
    if getattr(existing, "id", None) != expected_id:
        existing.id = expected_id
        changed = True
    if getattr(existing, "lane_branch_id", None) != lane_branch_id:
        existing.lane_branch_id = lane_branch_id
        changed = True
    if (getattr(existing, "lane_projection_hash", "") or "").strip() != lane_projection_hash:
        existing.lane_projection_hash = lane_projection_hash
        changed = True
    if getattr(existing, "enabled", None) != enabled:
        existing.enabled = enabled
        changed = True
    if getattr(existing, "mode", None) != mode:
        existing.mode = mode
        changed = True

    if not changed:
        return network_node_peer
    return network_node_peer
    # --- AWARE: LOGIC END upsert_fanout_rule


async def remove_fanout_rule(
    network_node_peer: NetworkNodePeer, lane_branch_id: UUID, lane_projection_hash: str
) -> NetworkNodePeer:
    """
    Remove a fan-out rule for this peer (v0).

    Contract:
    - Idempotent: removing a missing rule is a no-op.
    """

    # --- AWARE: LOGIC START remove_fanout_rule
    lane_projection_hash = (lane_projection_hash or "").strip()
    if not lane_projection_hash:
        return network_node_peer

    expected_id = stable_network_node_peer_fanout_rule_id(
        network_node_peer_id=network_node_peer.id,
        lane_branch_id=lane_branch_id,
        lane_projection_hash=lane_projection_hash,
    )

    rules = list(network_node_peer.fanout_rules or [])
    kept: list[NetworkNodePeerFanoutRule] = []
    for rule in rules:
        if getattr(rule, "id", None) == expected_id:
            continue
        if (
            getattr(rule, "lane_branch_id", None) == lane_branch_id
            and (getattr(rule, "lane_projection_hash", "") or "").strip() == lane_projection_hash
        ):
            continue
        kept.append(rule)
    if len(kept) == len(rules):
        return network_node_peer

    network_node_peer.fanout_rules = kept
    return network_node_peer
    # --- AWARE: LOGIC END remove_fanout_rule
