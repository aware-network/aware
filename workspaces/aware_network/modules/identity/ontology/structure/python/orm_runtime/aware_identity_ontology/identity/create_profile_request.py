from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology
from aware_identity_ontology.identity.identity_enums import IdentityType


class CreateProfileRequest(BaseModel):
    # Attributes
    display_name: str = Field(description="Display Name")
    public_handle: str
    full_name: str
    country_code: str
    language_code: str
    bio: str | None = Field(default=None)
    identity_type: IdentityType
    image_id: UUID | None = Field(default=None)
    image_sha: str | None = Field(default=None)
    image_mime_type: str | None = Field(default=None)
    image_size_bytes: int | None = Field(default=None)
