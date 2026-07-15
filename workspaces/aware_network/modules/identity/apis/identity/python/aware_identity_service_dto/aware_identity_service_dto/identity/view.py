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


class IdentityAdmissionViewStateV1(BaseModel):
    """
    API-owned view-state contract for first Identity admission.
    Public API view key: identity.identity_admission
    """

    # Attributes
    admitted: bool = Field(default=False)
    identity_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    identity_profile_id: UUID | None = Field(default=None)
    display_name: str | None = Field(default=None)
    public_handle: str | None = Field(default=None)
    bio: str | None = Field(default=None)
    status: str | None = Field(default=None)
    status_tone: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)
