from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Network Ontology
from aware_network_ontology.network.network_node_config import NetworkNodeConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_network_ontology.stable_ids import stable_network_node_config_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build(name: str, description: str | None = None) -> NetworkNodeConfig:
    """
    Create the canonical Network-owned semantic config root for a Node package.

    Notes:
    - `NetworkNodeConfig` is keyed by semantic node package identity, not by bootstrap secrets.
    - This root stays minimal and node-owned.
    - Workspace/deploy own hosted composition and runtime-target selection above this rail.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("NetworkNodeConfig.build requires non-empty name")
    normalized_description = (description or "").strip() or None

    config_id = stable_network_node_config_id(name=normalized_name)

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    if session is not None:
        existing = session.imap_get(NetworkNodeConfig, config_id)
        if existing is not None:
            if existing.name != normalized_name:
                raise RuntimeError(
                    "NetworkNodeConfig.build name mismatch for existing config: "
                    f"network_node_config_id={config_id} "
                    f"existing={existing.name!r} provided={normalized_name!r}"
                )
            existing_description = (existing.description or "").strip() or None
            if existing_description != normalized_description:
                raise RuntimeError(
                    "NetworkNodeConfig.build description mismatch for existing config: "
                    f"network_node_config_id={config_id} "
                    f"existing={existing_description!r} provided={normalized_description!r}"
                )
            return existing

    return NetworkNodeConfig.model_construct(
        id=config_id,
        name=normalized_name,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build
