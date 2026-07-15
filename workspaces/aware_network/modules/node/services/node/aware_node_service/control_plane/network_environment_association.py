from __future__ import annotations

from uuid import UUID

from aware_types import JsonObject

from aware_node_service.control_plane.environment_host_support import (
    EnvironmentRouteHandler,
)


class NetworkNodeEnvironmentAssociationService:
    """Records deferred publication readiness without mutating Network ontology.

    Network Service owns the eventual NetworkNode and Environment association
    commits through reconcile_node_publication.
    """

    def __init__(
        self,
        *,
        route_to_environment_service: EnvironmentRouteHandler,
    ) -> None:
        self._route_to_environment_service = route_to_environment_service

    async def ensure_node_environment(
        self,
        *,
        actor_id: UUID | None,
        environment_id: UUID,
        node_id: UUID,
        process_id: UUID | None,
        thread_id: UUID | None,
        role: str = "owner",
        is_active: bool = True,
        priority: int = 100,
        timeout_s: float = 30.0,
    ) -> JsonObject:
        del actor_id, process_id, thread_id, timeout_s
        return JsonObject(
            {
                "status": "network_publication_pending",
                "node_id": str(node_id),
                "environment_id": str(environment_id),
                "role": role,
                "is_active": is_active,
                "priority": priority,
                "authority": "network-service.reconcile_node_publication",
            }
        )


__all__ = ["NetworkNodeEnvironmentAssociationService"]
