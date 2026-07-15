from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_storage_ontology_orm_models.blob.storage_blob import StorageBlob


class IdentityProfile(ORMModel):
    # Relationships
    image: StorageBlob | None = Field(default=None, exclude=True)

    # Attributes
    public_handle: str
    display_name: str
    full_name: str
    country_code: str
    language_code: str
    bio: str | None = Field(default=None)

    # Foreign Keys
    image_id: UUID | None = Field(default=None, description="Foreign key for IdentityProfile.image")
