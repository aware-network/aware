from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology
from aware_experience_ontology.turn.turn_enums import (
    TurnExecutionState,
    TurnExecutionTerminalStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology.turn.turn_feedback import TurnFeedback


class Turn(ORMModel):
    """
    Canonical runtime turn execution state (mailbox lifecycle truth).
    Contract:
    - Runtime owns lifecycle transitions (`accepted -> running -> terminal`).
    - Domain adapters submit/query turns via runtime APIs; they do not own a second state machine.
    - No hard coupling to `thread` in v0; thread alignment is a later explicit contract.
    """

    # Relationships
    feedbacks: list[TurnFeedback] = Field(default_factory=list, exclude=True)

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

    @classmethod
    async def build(
        cls,
        environment_id: UUID,
        target_actor_id: UUID,
        key: str,
        mailbox_key: str,
        max_attempts: int = 1,
        created_at_unix_ms: int | None = None,
        accepted_at_unix_ms: int | None = None,
        idempotency_key: str | None = None,
        cause_event_id: UUID | None = None,
        cause_action_execution_id: UUID | None = None,
        payload: JsonObject | None = None,
        resolved_branch_id: UUID | None = None,
        resolved_projection_hash: str | None = None,
        lane_resolution_source: str | None = None,
    ) -> Turn:
        """
        Construct a deterministic Turn instance for runtime turn execution lifecycle.

        Contract:
        - Identity is derived from `(environment_id, target_actor_id, key)`.
        - Constructor is idempotent for repeated calls with the same identity tuple.
        """

        payload = {
            "environment_id": environment_id,
            "target_actor_id": target_actor_id,
            "key": key,
            "mailbox_key": mailbox_key,
            "max_attempts": max_attempts,
            "created_at_unix_ms": created_at_unix_ms,
            "accepted_at_unix_ms": accepted_at_unix_ms,
            "idempotency_key": idempotency_key,
            "cause_event_id": cause_event_id,
            "cause_action_execution_id": cause_action_execution_id,
            "payload": payload,
            "resolved_branch_id": resolved_branch_id,
            "resolved_projection_hash": resolved_projection_hash,
            "lane_resolution_source": lane_resolution_source,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Turn):
            return value
        return Turn.validate_invocation_value(value)

    async def add_feedback(
        self,
        sequence: int,
        stage: str,
        status: str,
        created_at_unix_ms: int,
        message: str | None = None,
        payload: JsonObject | None = None,
    ) -> TurnFeedback:
        """
        Append one feedback record under this Turn.

        Contract:
        - Mutates only this Turn membership (`feedbacks`).
        - Feedback identity is deterministic per `(turn_id, sequence)`.
        """

        payload = {
            "sequence": sequence,
            "stage": stage,
            "status": status,
            "created_at_unix_ms": created_at_unix_ms,
            "message": message,
            "payload": payload,
        }
        result = await invoke_instance(orm_model=self, function_name="add_feedback", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.turn.turn_feedback import TurnFeedback

        if isinstance(value, TurnFeedback):
            return value
        return TurnFeedback.validate_invocation_value(value)

    async def set_lane_resolution(
        self, resolved_branch_id: UUID, resolved_projection_hash: str, lane_resolution_source: str | None = None
    ) -> Turn:
        """
        Persist runtime-resolved execution lane on this Turn.

        Contract:
        - Runtime-owned lane resolution metadata only.
        - Idempotent for repeated writes of the same lane resolution.
        """

        payload = {
            "resolved_branch_id": resolved_branch_id,
            "resolved_projection_hash": resolved_projection_hash,
            "lane_resolution_source": lane_resolution_source,
        }
        result = await invoke_instance(orm_model=self, function_name="set_lane_resolution", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Turn):
            return value
        return Turn.validate_invocation_value(value)

    async def claim_running(
        self,
        attempt_count: int,
        started_at_unix_ms: int,
        lease_owner: str | None = None,
        lease_expires_at_unix_ms: int | None = None,
    ) -> Turn:
        """
        Transition this Turn to `running` for an execution attempt.

        Contract:
        - State becomes `running`.
        - `attempt_count` is runtime-owned and must be monotonic.
        """

        payload = {
            "attempt_count": attempt_count,
            "started_at_unix_ms": started_at_unix_ms,
            "lease_owner": lease_owner,
            "lease_expires_at_unix_ms": lease_expires_at_unix_ms,
        }
        result = await invoke_instance(orm_model=self, function_name="claim_running", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Turn):
            return value
        return Turn.validate_invocation_value(value)

    async def mark_retry_pending(
        self, attempt_count: int, accepted_at_unix_ms: int, error_code: str, error_message: str | None = None
    ) -> Turn:
        """
        Transition this Turn back to `accepted` after a retryable failure.

        Contract:
        - State becomes `accepted`.
        - Terminal fields are cleared.
        """

        payload = {
            "attempt_count": attempt_count,
            "accepted_at_unix_ms": accepted_at_unix_ms,
            "error_code": error_code,
            "error_message": error_message,
        }
        result = await invoke_instance(orm_model=self, function_name="mark_retry_pending", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Turn):
            return value
        return Turn.validate_invocation_value(value)

    async def finish_terminal(
        self,
        terminal_status: TurnExecutionTerminalStatus,
        terminal_at_unix_ms: int,
        result_summary: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        result_commit_ids: list[UUID] = [],
    ) -> Turn:
        """
        Transition this Turn to terminal.

        Contract:
        - State becomes `terminal`.
        - Terminal status and timing are written canonically on this Turn.
        """

        payload = {
            "terminal_status": terminal_status,
            "terminal_at_unix_ms": terminal_at_unix_ms,
            "result_summary": result_summary,
            "error_code": error_code,
            "error_message": error_message,
            "result_commit_ids": result_commit_ids,
        }
        result = await invoke_instance(orm_model=self, function_name="finish_terminal", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Turn):
            return value
        return Turn.validate_invocation_value(value)


class TurnBuildInput(BaseModel):
    environment_id: UUID
    target_actor_id: UUID
    key: str
    mailbox_key: str
    max_attempts: int = Field(default=1)
    created_at_unix_ms: int | None = Field(default=None)
    accepted_at_unix_ms: int | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    cause_event_id: UUID | None = Field(default=None)
    cause_action_execution_id: UUID | None = Field(default=None)
    payload: JsonObject | None = Field(default=None)
    resolved_branch_id: UUID | None = Field(default=None)
    resolved_projection_hash: str | None = Field(default=None)
    lane_resolution_source: str | None = Field(default=None)


class TurnBuildOutput(BaseModel):
    value: Turn


class TurnAddFeedbackInput(BaseModel):
    sequence: int
    stage: str
    status: str
    created_at_unix_ms: int
    message: str | None = Field(default=None)
    payload: JsonObject | None = Field(default=None)


class TurnAddFeedbackOutput(BaseModel):
    value: TurnFeedback


class TurnSetLaneResolutionInput(BaseModel):
    resolved_branch_id: UUID
    resolved_projection_hash: str
    lane_resolution_source: str | None = Field(default=None)


class TurnSetLaneResolutionOutput(BaseModel):
    value: Turn


class TurnClaimRunningInput(BaseModel):
    attempt_count: int
    started_at_unix_ms: int
    lease_owner: str | None = Field(default=None)
    lease_expires_at_unix_ms: int | None = Field(default=None)


class TurnClaimRunningOutput(BaseModel):
    value: Turn


class TurnMarkRetryPendingInput(BaseModel):
    attempt_count: int
    accepted_at_unix_ms: int
    error_code: str
    error_message: str | None = Field(default=None)


class TurnMarkRetryPendingOutput(BaseModel):
    value: Turn


class TurnFinishTerminalInput(BaseModel):
    terminal_status: TurnExecutionTerminalStatus
    terminal_at_unix_ms: int
    result_summary: str | None = Field(default=None)
    error_code: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    result_commit_ids: list[UUID] = Field(default_factory=list)


class TurnFinishTerminalOutput(BaseModel):
    value: Turn


FUNCTIONS = {
    "Turn": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Construct a deterministic Turn instance for runtime turn execution lifecycle.\n\nContract:\n- Identity is derived from `(environment_id, target_actor_id, key)`.\n- Constructor is idempotent for repeated calls with the same identity tuple.",
                "is_constructor": True,
            },
            "input": TurnBuildInput,
            "output": TurnBuildOutput,
        },
        "add_feedback": {
            "canonical": {
                "name": "add_feedback",
                "description": "Append one feedback record under this Turn.\n\nContract:\n- Mutates only this Turn membership (`feedbacks`).\n- Feedback identity is deterministic per `(turn_id, sequence)`.",
                "is_constructor": False,
            },
            "input": TurnAddFeedbackInput,
            "output": TurnAddFeedbackOutput,
        },
        "set_lane_resolution": {
            "canonical": {
                "name": "set_lane_resolution",
                "description": "Persist runtime-resolved execution lane on this Turn.\n\nContract:\n- Runtime-owned lane resolution metadata only.\n- Idempotent for repeated writes of the same lane resolution.",
                "is_constructor": False,
            },
            "input": TurnSetLaneResolutionInput,
            "output": TurnSetLaneResolutionOutput,
        },
        "claim_running": {
            "canonical": {
                "name": "claim_running",
                "description": "Transition this Turn to `running` for an execution attempt.\n\nContract:\n- State becomes `running`.\n- `attempt_count` is runtime-owned and must be monotonic.",
                "is_constructor": False,
            },
            "input": TurnClaimRunningInput,
            "output": TurnClaimRunningOutput,
        },
        "mark_retry_pending": {
            "canonical": {
                "name": "mark_retry_pending",
                "description": "Transition this Turn back to `accepted` after a retryable failure.\n\nContract:\n- State becomes `accepted`.\n- Terminal fields are cleared.",
                "is_constructor": False,
            },
            "input": TurnMarkRetryPendingInput,
            "output": TurnMarkRetryPendingOutput,
        },
        "finish_terminal": {
            "canonical": {
                "name": "finish_terminal",
                "description": "Transition this Turn to terminal.\n\nContract:\n- State becomes `terminal`.\n- Terminal status and timing are written canonically on this Turn.",
                "is_constructor": False,
            },
            "input": TurnFinishTerminalInput,
            "output": TurnFinishTerminalOutput,
        },
    },
}

__all__ = [
    "Turn",
    "TurnBuildInput",
    "TurnBuildOutput",
    "TurnAddFeedbackInput",
    "TurnAddFeedbackOutput",
    "TurnSetLaneResolutionInput",
    "TurnSetLaneResolutionOutput",
    "TurnClaimRunningInput",
    "TurnClaimRunningOutput",
    "TurnMarkRetryPendingInput",
    "TurnMarkRetryPendingOutput",
    "TurnFinishTerminalInput",
    "TurnFinishTerminalOutput",
    "FUNCTIONS",
]
