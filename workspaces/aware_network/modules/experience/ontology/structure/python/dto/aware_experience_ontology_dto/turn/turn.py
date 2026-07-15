from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology Dto
from aware_experience_ontology_dto.turn.turn_enums import (
    TurnExecutionState,
    TurnExecutionTerminalStatus,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology_dto.turn.turn_feedback import TurnFeedback


class Turn(BaseModel):
    """
    Canonical runtime turn execution state (mailbox lifecycle truth).
    Contract:
    - Runtime owns lifecycle transitions (`accepted -> running -> terminal`).
    - Domain adapters submit/query turns via runtime APIs; they do not own a second state machine.
    - No hard coupling to `thread` in v0; thread alignment is a later explicit contract.
    """

    # Relationships
    feedbacks: list[TurnFeedback] = Field(default_factory=list)

    # Attributes
    environment_id: UUID
    key: str
    mailbox_key: str
    state: TurnExecutionState = Field(default=TurnExecutionState.accepted)
    terminal_status: TurnExecutionTerminalStatus | None = Field(default=None)
    target_actor_id: UUID
    resolved_branch_id: UUID | None = Field(default=None)
    resolved_projection_hash: str | None = Field(default=None)
    lane_resolution_source: str | None = Field(default=None)
    created_at_unix_ms: int
    accepted_at_unix_ms: int
    started_at_unix_ms: int | None = Field(default=None)
    terminal_at_unix_ms: int | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    cause_event_id: UUID | None = Field(default=None)
    cause_action_execution_id: UUID | None = Field(default=None)
    attempt_count: int = Field(default=0)
    max_attempts: int = Field(default=1)
    lease_owner: str | None = Field(default=None)
    lease_expires_at_unix_ms: int | None = Field(default=None)
    error_code: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    result_summary: str | None = Field(default=None)
    result_commit_ids: list[UUID] = Field(default_factory=list)
    payload: JsonObject | None = Field(default=None)
