from __future__ import annotations

from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class InvokeFunctionCallTarget(Enum):
    instance = "instance"
    opg_constructor = "opg_constructor"


class InvokeFunctionRequest(BaseModel):
    operation: Literal["invoke_function"] = "invoke_function"
    actor_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    call_target: InvokeFunctionCallTarget = Field(
        default=InvokeFunctionCallTarget.instance
    )
    object_id: UUID | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    function_id: UUID
    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)
    expected_graph_hash_pre: str | None = Field(default=None)
    expected_head_commit_id: UUID | None = Field(default=None)
    commit: bool = Field(default=True)
    publish: bool = Field(default=False)


class LaneNotificationContext(BaseModel):
    actor_id: UUID | None = Field(default=None)
    branch_id: UUID
    projection_hash: str


class LaneCommitReceiptNotification(LaneNotificationContext):
    operation: Literal["lane_commit_receipt"] = "lane_commit_receipt"
    commit_id: UUID
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    object_instance_graph_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    created_at_unix_ms: int | None = Field(default=None)
    operation_label: str | None = Field(default=None)
    call_target: InvokeFunctionCallTarget | None = Field(default=None)
    function_id: UUID | None = Field(default=None)
    object_id: UUID | None = Field(default=None)
    class_instance_identity_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    head_version: int | None = Field(default=None)


class LaneEventReceiptNotification(LaneNotificationContext):
    operation: Literal["lane_event_receipt"] = "lane_event_receipt"
    event_id: UUID
    event_type: str
    source: str
    created_at_unix_ms: int
    commit_id: UUID
    target_actor_id: UUID | None = Field(default=None)
    actor_subscription_id: UUID | None = Field(default=None)
    event_config_condition_config_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)


class LaneActionExecutionReceiptNotification(LaneNotificationContext):
    operation: Literal["lane_action_execution_receipt"] = (
        "lane_action_execution_receipt"
    )
    action_execution_id: UUID
    event_id: UUID
    event_type: str
    source: str
    created_at_unix_ms: int
    commit_id: UUID
    target_actor_id: UUID | None = Field(default=None)
    actor_subscription_id: UUID | None = Field(default=None)
    event_config_condition_config_id: UUID | None = Field(default=None)
    action_binding_id: UUID | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_type: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)


class LaneActionFeedbackReceiptNotification(LaneNotificationContext):
    operation: Literal["lane_action_feedback_receipt"] = (
        "lane_action_feedback_receipt"
    )
    action_execution_id: UUID
    event_id: UUID
    sequence: int
    created_at_unix_ms: int
    stage: str
    status: str
    action_binding_id: UUID | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_type: str | None = Field(default=None)
    message: str | None = Field(default=None)
    actor_identity_id: UUID | None = Field(default=None)
    execution_request_id: UUID | None = Field(default=None)


class LaneActionTerminalReceiptNotification(LaneNotificationContext):
    operation: Literal["lane_action_terminal_receipt"] = (
        "lane_action_terminal_receipt"
    )
    action_execution_id: UUID
    event_id: UUID
    terminal_status: str
    handled: bool
    created_at_unix_ms: int
    action_binding_id: UUID | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_type: str | None = Field(default=None)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
    actor_identity_id: UUID | None = Field(default=None)
    execution_request_id: UUID | None = Field(default=None)


class LaneTurnStreamReceiptNotification(LaneNotificationContext):
    operation: Literal["lane_turn_stream_receipt"] = "lane_turn_stream_receipt"
    service: str
    inference_request_id: UUID
    created_at_unix_ms: int
    stream_kind: str
    sequence: int | None = Field(default=None)
    agent_identity_id: UUID | None = Field(default=None)
    text_delta: str | None = Field(default=None)
    message: str | None = Field(default=None)
    payload: Any | None = Field(default=None)


__all__ = [
    "InvokeFunctionCallTarget",
    "InvokeFunctionRequest",
    "LaneActionExecutionReceiptNotification",
    "LaneActionFeedbackReceiptNotification",
    "LaneActionTerminalReceiptNotification",
    "LaneCommitReceiptNotification",
    "LaneEventReceiptNotification",
    "LaneNotificationContext",
    "LaneTurnStreamReceiptNotification",
]
