from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Service Dto
from aware_reactivity_service_dto.reactivity.action_feedback_enums import (
    ActionFeedbackStage,
    ActionFeedbackStatus,
)

# Types
from aware_types import JsonValue


class ActionFeedback(BaseModel):
    """
    Canonical DTO for progressive action execution feedback.
    Contract:
    - `stage` is constrained by `ActionFeedbackStage`.
    - `status` is constrained by `ActionFeedbackStatus`.
    - Caller attribution lives above this rail in request context or
    provenance receipts.
    - v0 emits:
    - stage=dispatch status=requested
    - stage=execute status=running|responded|skipped|failed
    """

    # Attributes
    action_feedback_id: UUID | None = Field(default=None)
    action_intent_id: UUID | None = Field(default=None)
    action_execution_id: UUID
    event_id: UUID
    sequence: int
    created_at_unix_ms: int
    stage: ActionFeedbackStage
    status: ActionFeedbackStatus
    action_binding_id: UUID | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_type: str | None = Field(default=None)
    message: str | None = Field(default=None)
    payload: JsonValue | None = Field(default=None)
    executor_ref: str | None = Field(default=None)
    result_info: str | None = Field(default=None)
    execution_request_id: UUID | None = Field(default=None)
