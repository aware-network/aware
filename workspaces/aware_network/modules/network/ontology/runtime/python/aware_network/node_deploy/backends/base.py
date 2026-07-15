from __future__ import annotations

from typing import Protocol

from aware_network.node_deploy.dto import (
    DescribeNodeRuntimeRequest,
    EnsureNodeRuntimeStartedRequest,
    RestartNodeRuntimeRequest,
    StopNodeRuntimeRequest,
    StreamNodeRuntimeEventsRequest,
    TailNodeRuntimeLogsRequest,
)

from aware_network.node_deploy.contracts import NodeDeployEventSink
from aware_network.node_deploy.models import (
    NodeDeployLogTail,
    NodeDeployRuntimeSnapshot,
)


class NodeDeployBackend(Protocol):
    """Backend interface for concrete repo-dev, installed, or remote supervisors."""

    async def describe_runtime(
        self,
        *,
        request: DescribeNodeRuntimeRequest,
    ) -> NodeDeployRuntimeSnapshot: ...

    async def ensure_runtime_started(
        self,
        *,
        request: EnsureNodeRuntimeStartedRequest,
        event_sink: NodeDeployEventSink | None = None,
    ) -> NodeDeployRuntimeSnapshot: ...

    async def restart_runtime(
        self,
        *,
        request: RestartNodeRuntimeRequest,
        event_sink: NodeDeployEventSink | None = None,
    ) -> NodeDeployRuntimeSnapshot: ...

    async def stop_runtime(
        self,
        *,
        request: StopNodeRuntimeRequest,
        event_sink: NodeDeployEventSink | None = None,
    ) -> NodeDeployRuntimeSnapshot: ...

    async def tail_runtime_logs(
        self,
        *,
        request: TailNodeRuntimeLogsRequest,
    ) -> NodeDeployLogTail: ...

    async def stream_runtime_events(
        self,
        *,
        request: StreamNodeRuntimeEventsRequest,
        event_sink: NodeDeployEventSink,
    ) -> NodeDeployRuntimeSnapshot: ...
