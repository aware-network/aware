from __future__ import annotations

from uuid import UUID

from aware_utils.logging import logger

from aware_node_service.control_plane.environment_host_support import (
    EnvironmentRouteHandler,
)


class NetworkNodeTopologyBootstrapService:
    """Defers Network topology publication to the Network Service authority."""

    def __init__(self, *, route_to_environment_service: EnvironmentRouteHandler):
        self._route_to_environment_service = route_to_environment_service

    async def bootstrap_network_topology(
        self,
        *,
        actor_id: UUID | None,
        environment_id: UUID,
        process_id: UUID | None,
        thread_id: UUID | None,
    ) -> None:
        del actor_id, process_id, thread_id
        logger.info(
            "Network topology publication pending Network Service reconciliation "
            "(environment_id=%s)",
            environment_id,
        )


__all__ = ["NetworkNodeTopologyBootstrapService"]
