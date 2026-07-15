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

from aware_network.node_deploy.models import NodeDeployRuntimeSnapshot


class NodeDeploySupervisorError(RuntimeError):
    """Canonical supervisor exception that may carry the last known runtime state."""

    def __init__(
        self,
        message: str,
        *,
        runtime_status: NodeDeployRuntimeSnapshot | None = None,
    ) -> None:
        super().__init__(message)
        self.runtime_status = runtime_status


def build_failure_response(
    *,
    request: NodeDeployOperationRequest,
    error: Exception | str,
    runtime_status: NodeDeployRuntimeSnapshot | None = None,
) -> NodeDeployOperationResponse:
    message = str(error)
    status_model = runtime_status.to_api_model() if runtime_status else None
    if isinstance(request, DescribeNodeRuntimeRequest):
        return DescribeNodeRuntimeResponse(
            actor_id=request.actor_id,
            status="failed",
            error=message,
            runtime_status=status_model,
        )
    if isinstance(request, EnsureNodeRuntimeStartedRequest):
        return EnsureNodeRuntimeStartedResponse(
            actor_id=request.actor_id,
            status="failed",
            error=message,
            runtime_status=status_model,
        )
    if isinstance(request, RestartNodeRuntimeRequest):
        return RestartNodeRuntimeResponse(
            actor_id=request.actor_id,
            status="failed",
            error=message,
            runtime_status=status_model,
        )
    if isinstance(request, StopNodeRuntimeRequest):
        return StopNodeRuntimeResponse(
            actor_id=request.actor_id,
            status="failed",
            error=message,
            runtime_status=status_model,
        )
    if isinstance(request, TailNodeRuntimeLogsRequest):
        return TailNodeRuntimeLogsResponse(
            actor_id=request.actor_id,
            status="failed",
            error=message,
            runtime_status=status_model,
            log_lines=[],
        )
    if isinstance(request, StreamNodeRuntimeEventsRequest):
        return StreamNodeRuntimeEventsResponse(
            actor_id=request.actor_id,
            status="failed",
            error=message,
            runtime_status=status_model,
            stream_open=False,
        )
    raise TypeError(f"Unsupported NodeDeployOperationRequest type: {type(request)!r}")
