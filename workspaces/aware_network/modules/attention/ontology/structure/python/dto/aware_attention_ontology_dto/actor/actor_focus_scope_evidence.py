from __future__ import annotations

# Standard
from datetime import datetime
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class ActorFocusScopeEvidence(BaseModel):
    """Attention-owned evidence row that contributes to an ActorFocusScope weight."""

    # Attributes
    evidence_key: str
    kind: str
    source_type: str | None = Field(default=None)
    source_id: UUID | None = Field(default=None)
    source_key: str | None = Field(default=None)
    weight_delta: float = Field(default=0.0)
    confidence: float | None = Field(default=None)
    observed_at: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    rationale: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)
