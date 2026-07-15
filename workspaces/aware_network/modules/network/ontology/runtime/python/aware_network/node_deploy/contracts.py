from __future__ import annotations

from typing import Protocol

from aware_network.node_deploy.dto import (
    NodeDeployOperationEvent,
    NodeDeployOperationRequest,
    NodeDeployOperationResponse,
)


class NodeDeployEventSink(Protocol):
    """Host-neutral stream sink for deploy progress updates."""

    async def publish_event(self, *, event: NodeDeployOperationEvent) -> None: ...


class NodeDeploySupervisor(Protocol):
    """Canonical request dispatcher for pre-node deploy operations."""

    async def handle_request(
        self,
        *,
        request: NodeDeployOperationRequest,
        event_sink: NodeDeployEventSink | None = None,
    ) -> NodeDeployOperationResponse: ...
