from __future__ import annotations

# Standard
from enum import Enum
from functools import lru_cache
from typing import (
    ClassVar,
    Literal,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
    SerializeAsAny,
    field_validator,
    model_validator,
)


class NodeDeployRuntimePhase(Enum):
    """
    Transport-agnostic DTOs for pre-node deploy supervisor operations.
    IMPORTANT:
    - This contract is a peer rail to live-node `NetworkNodeOperation`.
    - It exists before a node websocket is available.
    - `local` vs `remote` remains a transport/backend concern, not an API fork.
    """

    idle = "idle"
    starting_bundle = "starting_bundle"
    start_db = "start_db"
    starting_environment = "starting_environment"
    waiting_environment = "waiting_environment"
    starting_node = "starting_node"
    waiting_node = "waiting_node"
    ready = "ready"
    failed = "failed"


class NodeDeployTarget(BaseModel):
    # Attributes
    target_id: UUID | None = Field(default=None)
    target_key: str | None = Field(default=None)
    display_name: str | None = Field(default=None)
    node_base_url: str | None = Field(default=None)
    node_websocket_path: str | None = Field(default=None)


class NodeDeployTargetStatus(BaseModel):
    # Attributes
    target_id: str
    display_name: str
    kind: str | None = Field(default=None)
    endpoint: str | None = Field(default=None)
    phase: str = Field(default="idle")
    is_active: bool = Field(default=False)
    is_healthy: bool = Field(default=False)
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    detail_lines: list[str] = Field(default_factory=list)


class NodeDeployRuntimeStatus(BaseModel):
    # Attributes
    target: NodeDeployTarget | None = Field(default=None)
    phase: NodeDeployRuntimePhase = Field(default=NodeDeployRuntimePhase.idle)
    active_target_id: str | None = Field(default=None)
    backend_kind: str | None = Field(default=None)
    is_active: bool = Field(default=False)
    is_healthy: bool = Field(default=False)
    node_base_url: str | None = Field(default=None)
    node_websocket_path: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    recent_log_lines: list[str] = Field(default_factory=list)
    target_statuses: list[NodeDeployTargetStatus] = Field(default_factory=list)


class NodeDeployOperationContext(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)


class NodeDeployOperation(BaseModel):
    # Attributes
    request: SerializeAsAny[NodeDeployOperationRequest] | None = Field(default=None)
    response: SerializeAsAny[NodeDeployOperationResponse] | None = Field(default=None)
    stream_item: SerializeAsAny[NodeDeployOperationEvent] | None = Field(default=None)

    @field_validator("request", mode="before")
    @classmethod
    def _parse_request(cls, v):
        if v is None:
            return None
        return NodeDeployOperationRequest.parse(v)

    @field_validator("response", mode="before")
    @classmethod
    def _parse_response(cls, v):
        if v is None:
            return None
        return NodeDeployOperationResponse.parse(v)

    @field_validator("stream_item", mode="before")
    @classmethod
    def _parse_stream_item(cls, v):
        if v is None:
            return None
        return NodeDeployOperationEvent.parse(v)

    @model_validator(mode="after")
    def _validate_oneof_0(self):
        if (
            sum(
                v is not None
                for v in (
                    self.request,
                    self.response,
                    self.stream_item,
                )
            )
            != 1
        ):
            raise ValueError("Exactly one of request, response, stream_item must be set")
        return self


class NodeDeployOperationRequest(NodeDeployOperationContext):
    # Discriminator Key
    operation: str

    # Attributes
    target: NodeDeployTarget | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "describe_node_runtime": "aware_network_service_dto.comms.models.node_deploy_operation.DescribeNodeRuntimeRequest",
        "ensure_node_runtime_started": "aware_network_service_dto.comms.models.node_deploy_operation.EnsureNodeRuntimeStartedRequest",
        "restart_node_runtime": "aware_network_service_dto.comms.models.node_deploy_operation.RestartNodeRuntimeRequest",
        "stop_node_runtime": "aware_network_service_dto.comms.models.node_deploy_operation.StopNodeRuntimeRequest",
        "tail_node_runtime_logs": "aware_network_service_dto.comms.models.node_deploy_operation.TailNodeRuntimeLogsRequest",
        "stream_node_runtime_events": "aware_network_service_dto.comms.models.node_deploy_operation.StreamNodeRuntimeEventsRequest",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownNodeDeployOperationRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownNodeDeployOperationRequest(NodeDeployOperationRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class NodeDeployOperationResponse(NodeDeployOperationContext):
    # Discriminator Key
    operation: str

    # Attributes
    status: str = Field(default="pending")
    error: str | None = Field(default=None)
    runtime_status: NodeDeployRuntimeStatus | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "describe_node_runtime": "aware_network_service_dto.comms.models.node_deploy_operation.DescribeNodeRuntimeResponse",
        "ensure_node_runtime_started": "aware_network_service_dto.comms.models.node_deploy_operation.EnsureNodeRuntimeStartedResponse",
        "restart_node_runtime": "aware_network_service_dto.comms.models.node_deploy_operation.RestartNodeRuntimeResponse",
        "stop_node_runtime": "aware_network_service_dto.comms.models.node_deploy_operation.StopNodeRuntimeResponse",
        "tail_node_runtime_logs": "aware_network_service_dto.comms.models.node_deploy_operation.TailNodeRuntimeLogsResponse",
        "stream_node_runtime_events": "aware_network_service_dto.comms.models.node_deploy_operation.StreamNodeRuntimeEventsResponse",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownNodeDeployOperationResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownNodeDeployOperationResponse(NodeDeployOperationResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class NodeDeployOperationEvent(NodeDeployOperationContext):
    # Discriminator Key
    kind: str

    # Attributes
    operation: str | None = Field(default=None)
    runtime_status: NodeDeployRuntimeStatus | None = Field(default=None)
    message: str | None = Field(default=None)
    timestamp: str | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "kind"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "runtime_status": "aware_network_service_dto.comms.models.node_deploy_operation.NodeDeployRuntimeStatusEvent",
        "runtime_log": "aware_network_service_dto.comms.models.node_deploy_operation.NodeDeployRuntimeLogEvent",
        "runtime_terminal": "aware_network_service_dto.comms.models.node_deploy_operation.NodeDeployRuntimeTerminalEvent",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownNodeDeployOperationEvent.model_validate(v)
        return cls.model_validate(v)


class UnknownNodeDeployOperationEvent(NodeDeployOperationEvent):
    """Forward-compatible fallback when `kind` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class DescribeNodeRuntimeRequest(NodeDeployOperationRequest):
    # Discriminator Tag
    operation: Literal["describe_node_runtime"] = "describe_node_runtime"


class DescribeNodeRuntimeResponse(NodeDeployOperationResponse):
    # Discriminator Tag
    operation: Literal["describe_node_runtime"] = "describe_node_runtime"


class EnsureNodeRuntimeStartedRequest(NodeDeployOperationRequest):
    # Discriminator Tag
    operation: Literal["ensure_node_runtime_started"] = "ensure_node_runtime_started"

    # Attributes
    wait_for_ready: bool = Field(default=True)


class EnsureNodeRuntimeStartedResponse(NodeDeployOperationResponse):
    # Discriminator Tag
    operation: Literal["ensure_node_runtime_started"] = "ensure_node_runtime_started"


class RestartNodeRuntimeRequest(NodeDeployOperationRequest):
    # Discriminator Tag
    operation: Literal["restart_node_runtime"] = "restart_node_runtime"

    # Attributes
    wait_for_ready: bool = Field(default=True)


class RestartNodeRuntimeResponse(NodeDeployOperationResponse):
    # Discriminator Tag
    operation: Literal["restart_node_runtime"] = "restart_node_runtime"


class StopNodeRuntimeRequest(NodeDeployOperationRequest):
    # Discriminator Tag
    operation: Literal["stop_node_runtime"] = "stop_node_runtime"

    # Attributes
    force: bool = Field(default=False)


class StopNodeRuntimeResponse(NodeDeployOperationResponse):
    # Discriminator Tag
    operation: Literal["stop_node_runtime"] = "stop_node_runtime"


class TailNodeRuntimeLogsRequest(NodeDeployOperationRequest):
    # Discriminator Tag
    operation: Literal["tail_node_runtime_logs"] = "tail_node_runtime_logs"

    # Attributes
    line_count: int = Field(default=200)


class TailNodeRuntimeLogsResponse(NodeDeployOperationResponse):
    # Discriminator Tag
    operation: Literal["tail_node_runtime_logs"] = "tail_node_runtime_logs"

    # Attributes
    log_lines: list[str] = Field(default_factory=list)


class StreamNodeRuntimeEventsRequest(NodeDeployOperationRequest):
    # Discriminator Tag
    operation: Literal["stream_node_runtime_events"] = "stream_node_runtime_events"

    # Attributes
    include_history: bool = Field(default=True)


class StreamNodeRuntimeEventsResponse(NodeDeployOperationResponse):
    # Discriminator Tag
    operation: Literal["stream_node_runtime_events"] = "stream_node_runtime_events"

    # Attributes
    stream_open: bool = Field(default=True)


class NodeDeployRuntimeStatusEvent(NodeDeployOperationEvent):
    # Discriminator Tag
    kind: Literal["runtime_status"] = "runtime_status"


class NodeDeployRuntimeLogEvent(NodeDeployOperationEvent):
    # Discriminator Tag
    kind: Literal["runtime_log"] = "runtime_log"

    # Attributes
    log_line: str | None = Field(default=None)


class NodeDeployRuntimeTerminalEvent(NodeDeployOperationEvent):
    # Discriminator Tag
    kind: Literal["runtime_terminal"] = "runtime_terminal"

    # Attributes
    terminal_status: str = Field(default="succeeded")
