from __future__ import annotations

from uuid import UUID, NAMESPACE_URL, uuid5


def resolve_node_system_actor_id() -> UUID:
    """Return the deterministic actor id for node-owned bootstrap operations."""

    return uuid5(NAMESPACE_URL, "aware:actor:system")


__all__ = ["resolve_node_system_actor_id"]
