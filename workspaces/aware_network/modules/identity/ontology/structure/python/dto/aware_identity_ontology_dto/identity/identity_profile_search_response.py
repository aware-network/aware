from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class IdentityProfileSearchResult(BaseModel):
    # Attributes
    identity_id: UUID
    identity_profile_id: UUID
    public_handle: str
    display_name: str
    full_name: str
    country_code: str
    language_code: str
    bio: str | None = Field(default=None)
    search_rank: float


class IdentityProfileSearchResponse(BaseModel):
    # Attributes
    results: list[IdentityProfileSearchResult] = Field(default_factory=list)
