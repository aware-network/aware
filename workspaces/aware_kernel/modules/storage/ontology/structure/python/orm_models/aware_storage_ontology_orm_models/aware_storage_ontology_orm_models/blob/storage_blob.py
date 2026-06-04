from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_storage_ontology_orm_models.bucket.storage_bucket import StorageBucket


class StorageBlob(ORMModel):
    # Relationships
    bucket: StorageBucket | None = Field(default=None, exclude=True)

    # Attributes
    mime_type: str
    object_key: str | None = Field(default=None)
    path_local: str | None = Field(default=None)
    sha: str
    size_bytes: int

    # Foreign Keys
    bucket_id: UUID | None = Field(default=None, description="Foreign key for StorageBlob.bucket")
