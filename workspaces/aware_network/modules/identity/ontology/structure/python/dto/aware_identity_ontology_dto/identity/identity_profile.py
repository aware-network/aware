from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_storage_ontology_dto.blob.storage_blob import StorageBlob


class IdentityProfile(BaseModel):
    # Relationships
    image: StorageBlob | None = Field(default=None)

    # Attributes
    public_handle: str
    display_name: str
    full_name: str
    country_code: str
    language_code: str
    bio: str | None = Field(default=None)
