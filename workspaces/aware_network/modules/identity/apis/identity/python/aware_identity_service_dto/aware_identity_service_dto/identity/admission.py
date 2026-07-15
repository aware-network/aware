from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_service_dto.profile.requests import CreateProfileRequest


class IdentitySignupViaProfileRequest(BaseModel):
    """
    Canonical DTOs for the first public Identity admission boundary.
    Ownership:
    - Identity API: actor-admission request/receipt shape.
    - Identity API package: public API client and service-protocol binding over these DTOs.
    - Interface: consumer of the generated public client, not owner of the contract.
    """

    # Attributes
    public_key: str
    create_profile_request: CreateProfileRequest
    request_id: UUID | None = Field(default=None)
    source: str | None = Field(default=None)
