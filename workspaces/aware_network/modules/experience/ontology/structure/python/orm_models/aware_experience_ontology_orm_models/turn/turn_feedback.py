from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

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
