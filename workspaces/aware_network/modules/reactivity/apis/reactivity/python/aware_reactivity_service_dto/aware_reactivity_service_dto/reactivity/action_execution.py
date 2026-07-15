from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Service Dto
from aware_reactivity_service_dto.reactivity.action_feedback_enums import (
    ActionExecutionClaimStatus,
    ActionExecutionStatus,
)

# Types
from aware_types import (
    JsonObject,
    JsonValue,
)

if TYPE_CHECKING:
    from aware_reactivity_service_dto.reactivity.action_intent import ReactivityActionIntent


class ActionExecution(BaseModel):
    """
    Canonical DTO for one reactivity action execution correlation.
    Ownership:
    - Reactivity API owns lifecycle correlation contracts.
    - Runtime dispatchers produce this payload.
    - Action executors consume the correlated context.
    - Caller attribution lives above this rail in request context or
    provenance receipts.
    """

    # Attributes
    action_execution_id: UUID | None = Field(default=None)
    action_intent_id: UUID
    event_id: UUID
    event_type: str
    source: str
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    event_config_condition_config_id: UUID | None = Field(default=None)
    action_binding_id: UUID | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_type: str | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    execution_key: str = Field(default="primary")
    status: ActionExecutionStatus = Field(default=ActionExecutionStatus.created)
    execution_context: JsonValue | None = Field(default=None)
    api_call_id: UUID | None = Field(
        default=None,
        description="API receipt correlated to this execution attempt.\nThis is an evidence link to the API-owned ingress receipt. The request\nvalue itself lives once on `ApiCall.request_model`.",
    )
    executor_ref: str | None = Field(default=None)
    result_info: str | None = Field(default=None)


class ReactivityActionExecutionClaimRequest(BaseModel):
    """Claim one canonical execution attempt before crossing a provider boundary."""

    # Attributes
    request_id: UUID | None = Field(default=None)
    claimant_id: str
    intent: ReactivityActionIntent
    execution_key: str = Field(default="primary")
    execution_context: JsonObject = Field(default_factory=JsonObject)


class ReactivityActionExecutionClaimResponse(BaseModel):
    """Graph-backed claim result. Only `claimed` grants provider invocation."""

    # Attributes
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=False)
    claim_status: ActionExecutionClaimStatus | None = Field(default=None)
    action_execution: ActionExecution | None = Field(default=None)
    event_commit_id: UUID | None = Field(default=None)
    action_intent_commit_id: UUID | None = Field(default=None)
    action_execution_commit_id: UUID | None = Field(default=None)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
