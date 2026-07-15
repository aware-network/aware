from __future__ import annotations

from aware_network.node_deploy.dto import (
    DescribeNodeRuntimeRequest,
    DescribeNodeRuntimeResponse,
    EnsureNodeRuntimeStartedRequest,
    EnsureNodeRuntimeStartedResponse,
    NodeDeployOperationRequest,
    NodeDeployOperationResponse,
    RestartNodeRuntimeRequest,
    RestartNodeRuntimeResponse,
    StopNodeRuntimeRequest,
    StopNodeRuntimeResponse,
    StreamNodeRuntimeEventsRequest,
    StreamNodeRuntimeEventsResponse,
    TailNodeRuntimeLogsRequest,
    TailNodeRuntimeLogsResponse,
)

from aware_network.node_deploy.backends.base import NodeDeployBackend
from aware_network.node_deploy.contracts import NodeDeployEventSink, NodeDeploySupervisor
from aware_network.node_deploy.errors import (
    NodeDeploySupervisorError,
    build_failure_response,
)


class DefaultNodeDeploySupervisor(NodeDeploySupervisor):
    """Default request dispatcher for the node-deploy control plane."""

    def __init__(self, *, backend: NodeDeployBackend) -> None:
        self._backend = backend

    async def handle_request(
        self,
        *,
        request: NodeDeployOperationRequest,
        event_sink: NodeDeployEventSink | None = None,
    ) -> NodeDeployOperationResponse:
        try:
            if isinstance(request, DescribeNodeRuntimeRequest):
                runtime_status = await self._backend.describe_runtime(request=request)
                return DescribeNodeRuntimeResponse(
                    actor_id=request.actor_id,
                    status="succeeded",
                    runtime_status=runtime_status.to_api_model(),
                )
            if isinstance(request, EnsureNodeRuntimeStartedRequest):
                runtime_status = await self._backend.ensure_runtime_started(
                    request=request,
                    event_sink=event_sink,
                )
                return EnsureNodeRuntimeStartedResponse(
                    actor_id=request.actor_id,
                    status="succeeded",
                    runtime_status=runtime_status.to_api_model(),
                )
            if isinstance(request, RestartNodeRuntimeRequest):
                runtime_status = await self._backend.restart_runtime(
                    request=request,
                    event_sink=event_sink,
                )
                return RestartNodeRuntimeResponse(
                    actor_id=request.actor_id,
                    status="succeeded",
                    runtime_status=runtime_status.to_api_model(),
                )
            if isinstance(request, StopNodeRuntimeRequest):
                runtime_status = await self._backend.stop_runtime(
                    request=request,
                    event_sink=event_sink,
                )
                return StopNodeRuntimeResponse(
                    actor_id=request.actor_id,
                    status="succeeded",
                    runtime_status=runtime_status.to_api_model(),
                )
            if isinstance(request, TailNodeRuntimeLogsRequest):
                log_tail = await self._backend.tail_runtime_logs(request=request)
                return TailNodeRuntimeLogsResponse(
                    actor_id=request.actor_id,
                    status="succeeded",
                    runtime_status=(log_tail.runtime_status.to_api_model() if log_tail.runtime_status else None),
                    log_lines=list(log_tail.log_lines),
                )
            if isinstance(request, StreamNodeRuntimeEventsRequest):
                if event_sink is None:
                    raise NodeDeploySupervisorError("stream_node_runtime_events requires an event sink")
                runtime_status = await self._backend.stream_runtime_events(
                    request=request,
                    event_sink=event_sink,
                )
                return StreamNodeRuntimeEventsResponse(
                    actor_id=request.actor_id,
                    status="succeeded",
                    runtime_status=runtime_status.to_api_model(),
                    stream_open=True,
                )
            raise NodeDeploySupervisorError(f"Unsupported NodeDeployOperationRequest type: {type(request)!r}")
        except NodeDeploySupervisorError as exc:
            return build_failure_response(
                request=request,
                error=exc,
                runtime_status=exc.runtime_status,
            )
        except Exception as exc:  # pragma: no cover - fail-closed guard
            return build_failure_response(request=request, error=exc)
