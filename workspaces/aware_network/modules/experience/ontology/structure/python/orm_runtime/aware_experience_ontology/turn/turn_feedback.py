from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject


class TurnFeedback(ORMModel):
    """
    Canonical per-turn feedback records.
    Contract:
    - Sequence is monotonic per Turn.
    - Parent relation is declared by `Turn.feedbacks[]`.
    """

    # Attributes
    mailbox_key: str
    sequence: int
    stage: str
    status: str
    created_at_unix_ms: int
    message: str | None = Field(default=None)
    payload: JsonObject | None = Field(default=None)

    # Foreign Keys
    turn_id: UUID = Field(description="Foreign key for Turn.feedbacks")

    @classmethod
    async def create_via_turn(
        cls,
        turn_id: UUID,
        sequence: int,
        stage: str,
        status: str,
        created_at_unix_ms: int,
        message: str | None = None,
        payload: JsonObject | None = None,
    ) -> TurnFeedback:
        """
        Construct a deterministic feedback record under a Turn.

        Contract:
        - Identity is derived from `(turn_id, sequence)`.
        - Constructor is idempotent for repeated calls with the same pair.
        """

        payload = {
            "turn_id": turn_id,
            "sequence": sequence,
            "stage": stage,
            "status": status,
            "created_at_unix_ms": created_at_unix_ms,
            "message": message,
            "payload": payload,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_turn", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, TurnFeedback):
            return value
        return TurnFeedback.validate_invocation_value(value)


class TurnFeedbackCreateViaTurnInput(BaseModel):
    turn_id: UUID = Field(description="Foreign key for Turn.feedbacks")
    sequence: int
    stage: str
    status: str
    created_at_unix_ms: int
    message: str | None = Field(default=None)
    payload: JsonObject | None = Field(default=None)


class TurnFeedbackCreateViaTurnOutput(BaseModel):
    value: TurnFeedback


FUNCTIONS = {
    "TurnFeedback": {
        "create_via_turn": {
            "canonical": {
                "name": "create_via_turn",
                "description": "Construct a deterministic feedback record under a Turn.\n\nContract:\n- Identity is derived from `(turn_id, sequence)`.\n- Constructor is idempotent for repeated calls with the same pair.",
                "is_constructor": True,
            },
            "input": TurnFeedbackCreateViaTurnInput,
            "output": TurnFeedbackCreateViaTurnOutput,
        },
    },
}

__all__ = [
    "TurnFeedback",
    "TurnFeedbackCreateViaTurnInput",
    "TurnFeedbackCreateViaTurnOutput",
    "FUNCTIONS",
]
