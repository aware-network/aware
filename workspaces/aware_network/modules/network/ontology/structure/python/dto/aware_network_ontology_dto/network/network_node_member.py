from __future__ import annotations

# Standard
from datetime import datetime
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class NetworkNodeMember(BaseModel):
    # Attributes
    identity_id: UUID
    is_primary: bool = Field(default=True)
    last_sync_at: datetime = Field(default_factory=datetime.utcnow)
    managed_since: datetime = Field(default_factory=datetime.utcnow)
