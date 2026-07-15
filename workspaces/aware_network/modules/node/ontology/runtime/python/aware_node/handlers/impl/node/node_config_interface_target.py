from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Node Ontology
from aware_node_ontology.node.node_config_interface_target import NodeConfigInterfaceTarget

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface_ontology.interface.interface_config import InterfaceConfig
from aware_interface_ontology.stable_ids import stable_interface_config_id
from aware_node_ontology.stable_ids import stable_node_config_interface_target_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_node_config(node_config_id: UUID, interface_name: str) -> NodeConfigInterfaceTarget:
    """
    Create one Node-owned interface target by canonical interface name.

    Contract:
    - Parent `NodeConfig` scope is injected by propagation.
    - Identity is keyed by `(node_config_id, interface_name)`.
    - The target `InterfaceConfig` portal is resolved from `interface_name` without storing a
      raw relationship-id attribute as semantic source.
    """

    # --- AWARE: LOGIC START build_via_node_config
    normalized_interface_name = (interface_name or "").strip()
    if not normalized_interface_name:
        raise RuntimeError("NodeConfigInterfaceTarget.build_via_node_config requires non-empty interface_name")

    target_id = stable_interface_config_id(name=normalized_interface_name)
    association_id = stable_node_config_interface_target_id(
        node_config_id=node_config_id,
        interface_name=normalized_interface_name,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_interface_config = session.imap_get(InterfaceConfig, target_id) if session is not None else None

    if session is not None:
        existing = session.imap_get(NodeConfigInterfaceTarget, association_id)
        if existing is not None:
            if existing.node_config_id != node_config_id:
                raise RuntimeError(
                    "NodeConfigInterfaceTarget.build_via_node_config payload mismatch for existing target: "
                    f"node_config_interface_target_id={association_id}"
                )
            if existing.interface_config_id != target_id:
                raise RuntimeError(
                    "NodeConfigInterfaceTarget.build_via_node_config interface_config_id mismatch for existing target: "
                    f"node_config_interface_target_id={association_id}"
                )
            if (existing.interface_name or "").strip() != normalized_interface_name:
                raise RuntimeError(
                    "NodeConfigInterfaceTarget.build_via_node_config interface_name mismatch for existing target: "
                    f"node_config_interface_target_id={association_id}"
                )
            if existing.interface_config is None and resolved_interface_config is not None:
                existing.interface_config = resolved_interface_config
            return existing

    return NodeConfigInterfaceTarget.model_construct(
        id=association_id,
        node_config_id=node_config_id,
        interface_config=resolved_interface_config,
        interface_config_id=target_id,
        interface_name=normalized_interface_name,
    )
    # --- AWARE: LOGIC END build_via_node_config
