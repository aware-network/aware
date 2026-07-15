from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeAlias

from aware_network_service_dto.comms.models.node_deploy_operation import (
    DescribeNodeRuntimeRequest,
    DescribeNodeRuntimeResponse,
    EnsureNodeRuntimeStartedRequest,
    EnsureNodeRuntimeStartedResponse,
    NodeDeployOperationEvent,
    NodeDeployOperationRequest,
    NodeDeployOperationResponse,
    NodeDeployRuntimeLogEvent,
    NodeDeployRuntimePhase,
    NodeDeployRuntimeStatus,
    NodeDeployRuntimeStatusEvent,
    NodeDeployRuntimeTerminalEvent,
    NodeDeployTarget,
    NodeDeployTargetStatus,
    RestartNodeRuntimeRequest,
    RestartNodeRuntimeResponse,
    StopNodeRuntimeRequest,
    StopNodeRuntimeResponse,
    StreamNodeRuntimeEventsRequest,
    StreamNodeRuntimeEventsResponse,
    TailNodeRuntimeLogsRequest,
    TailNodeRuntimeLogsResponse,
)

_NodeDeployRequestModel: TypeAlias = (
    type[DescribeNodeRuntimeRequest]
    | type[EnsureNodeRuntimeStartedRequest]
    | type[RestartNodeRuntimeRequest]
    | type[StopNodeRuntimeRequest]
    | type[TailNodeRuntimeLogsRequest]
    | type[StreamNodeRuntimeEventsRequest]
)
_NodeDeployResponseModel: TypeAlias = (
    type[DescribeNodeRuntimeResponse]
    | type[EnsureNodeRuntimeStartedResponse]
    | type[RestartNodeRuntimeResponse]
    | type[StopNodeRuntimeResponse]
    | type[TailNodeRuntimeLogsResponse]
    | type[StreamNodeRuntimeEventsResponse]
)
_NodeDeployEventModel: TypeAlias = (
    type[NodeDeployRuntimeStatusEvent] | type[NodeDeployRuntimeLogEvent] | type[NodeDeployRuntimeTerminalEvent]
)

_REQUEST_MODELS_BY_OPERATION: dict[str, _NodeDeployRequestModel] = {
    "describe_node_runtime": DescribeNodeRuntimeRequest,
    "ensure_node_runtime_started": EnsureNodeRuntimeStartedRequest,
    "restart_node_runtime": RestartNodeRuntimeRequest,
    "stop_node_runtime": StopNodeRuntimeRequest,
    "tail_node_runtime_logs": TailNodeRuntimeLogsRequest,
    "stream_node_runtime_events": StreamNodeRuntimeEventsRequest,
}
_RESPONSE_MODELS_BY_OPERATION: dict[str, _NodeDeployResponseModel] = {
    "describe_node_runtime": DescribeNodeRuntimeResponse,
    "ensure_node_runtime_started": EnsureNodeRuntimeStartedResponse,
    "restart_node_runtime": RestartNodeRuntimeResponse,
    "stop_node_runtime": StopNodeRuntimeResponse,
    "tail_node_runtime_logs": TailNodeRuntimeLogsResponse,
    "stream_node_runtime_events": StreamNodeRuntimeEventsResponse,
}
_EVENT_MODELS_BY_KIND: dict[str, _NodeDeployEventModel] = {
    "runtime_status": NodeDeployRuntimeStatusEvent,
    "runtime_log": NodeDeployRuntimeLogEvent,
    "runtime_terminal": NodeDeployRuntimeTerminalEvent,
}


def parse_node_deploy_operation_request(
    payload: Mapping[str, Any],
) -> NodeDeployOperationRequest:
    operation = payload.get("operation")
    if not isinstance(operation, str):
        raise ValueError("node_deploy request requires string field 'operation'")
    model = _REQUEST_MODELS_BY_OPERATION.get(operation)
    if model is None:
        raise ValueError(f"unknown node_deploy operation: {operation!r}")
    return model.model_validate(dict(payload))


def parse_node_deploy_operation_response(
    payload: Mapping[str, Any],
) -> NodeDeployOperationResponse:
    operation = payload.get("operation")
    if not isinstance(operation, str):
        raise ValueError("node_deploy response requires string field 'operation'")
    model = _RESPONSE_MODELS_BY_OPERATION.get(operation)
    if model is None:
        raise ValueError(f"unknown node_deploy operation: {operation!r}")
    return model.model_validate(dict(payload))


def parse_node_deploy_operation_event(
    payload: Mapping[str, Any],
) -> NodeDeployOperationEvent:
    kind = payload.get("kind")
    if not isinstance(kind, str):
        raise ValueError("node_deploy event requires string field 'kind'")
    model = _EVENT_MODELS_BY_KIND.get(kind)
    if model is None:
        raise ValueError(f"unknown node_deploy event kind: {kind!r}")
    return model.model_validate(dict(payload))


__all__ = [
    "DescribeNodeRuntimeRequest",
    "DescribeNodeRuntimeResponse",
    "EnsureNodeRuntimeStartedRequest",
    "EnsureNodeRuntimeStartedResponse",
    "NodeDeployOperationEvent",
    "NodeDeployOperationRequest",
    "NodeDeployOperationResponse",
    "NodeDeployRuntimeLogEvent",
    "NodeDeployRuntimePhase",
    "NodeDeployRuntimeStatus",
    "NodeDeployRuntimeStatusEvent",
    "NodeDeployRuntimeTerminalEvent",
    "NodeDeployTarget",
    "NodeDeployTargetStatus",
    "RestartNodeRuntimeRequest",
    "RestartNodeRuntimeResponse",
    "StopNodeRuntimeRequest",
    "StopNodeRuntimeResponse",
    "StreamNodeRuntimeEventsRequest",
    "StreamNodeRuntimeEventsResponse",
    "TailNodeRuntimeLogsRequest",
    "TailNodeRuntimeLogsResponse",
    "parse_node_deploy_operation_event",
    "parse_node_deploy_operation_request",
    "parse_node_deploy_operation_response",
]
