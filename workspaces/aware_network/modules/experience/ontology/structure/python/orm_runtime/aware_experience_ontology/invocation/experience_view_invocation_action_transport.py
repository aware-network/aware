from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class ExperienceViewInvocationActionRequest(BaseModel):
    """
    API-facing transport contract for invoking one Experience view action.
    Contract:
    - Generated Experience view APIs use this as endpoint request shape.
    - The actual invocation is still handled by the Experience service rail and
    recorded as `ExperienceInvocationAction`.
    - This type exists in the Experience ontology graph so generated view APIs do
    not depend on service DTO package materialization.
    """

    # Attributes
    experience_name: str
    projection_experience_view_instance_id: UUID | None = Field(default=None)
    view_invocation_action_config_id: UUID | None = Field(default=None)
    invocation_key: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    action_key: str | None = Field(default=None)
    request_ref: str | None = Field(default=None)
    receipt_ref: str | None = Field(default=None)
    request_payload: JsonObject = Field(default_factory=JsonObject)


class ExperienceViewInvocationActionResponse(BaseModel):
    """
    API-facing transport response for one Experience view action invocation.
    Contract:
    - Generated Experience view APIs use this as endpoint response shape.
    - Concrete receipt truth remains on `ExperienceInvocationAction` and related
    API/SDK receipts.
    """

    # Attributes
    success: bool = Field(default=False)
    status: str = Field(default="pending")
    experience_invocation_action_id: UUID | None = Field(default=None)
    api_call_id: UUID | None = Field(default=None)
    sdk_operation_call_id: UUID | None = Field(default=None)
    error: str | None = Field(default=None)
    receipt_payload: JsonObject = Field(default_factory=JsonObject)
