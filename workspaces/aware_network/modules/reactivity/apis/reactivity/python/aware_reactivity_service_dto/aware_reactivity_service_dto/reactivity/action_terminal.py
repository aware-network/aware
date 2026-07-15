from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Service Dto
from aware_reactivity_service_dto.reactivity.action_feedback_enums import ActionTerminalStatus


class ActionTerminal(BaseModel):
    """
    Canonical DTO for action execution terminal status.
    Caller attribution lives above this rail in request context or provenance
    receipts.
    """

    # Attributes
    action_execution_id: UUID
    event_id: UUID
    terminal_status: ActionTerminalStatus
    handled: bool
    created_at_unix_ms: int
    action_binding_id: UUID | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_type: str | None = Field(default=None)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
    execution_request_id: UUID | None = Field(default=None)
