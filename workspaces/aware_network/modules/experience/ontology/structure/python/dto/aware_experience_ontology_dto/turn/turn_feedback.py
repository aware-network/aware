from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class TurnFeedback(BaseModel):
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
