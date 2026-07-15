from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class IdentityAdmissionReceipt(BaseModel):
    """Canonical DTOs for first public Identity admission receipts."""

    # Attributes
    identity_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    identity_profile_id: UUID | None = Field(default=None)
    public_handle: str | None = Field(default=None)
    info: str | None = Field(default=None)
