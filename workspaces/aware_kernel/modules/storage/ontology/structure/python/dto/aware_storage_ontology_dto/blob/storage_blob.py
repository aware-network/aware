from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_storage_ontology_dto.bucket.storage_bucket import StorageBucket


class StorageBlob(BaseModel):
    # Relationships
    bucket: StorageBucket | None = Field(default=None)

    # Attributes
    mime_type: str
    object_key: str | None = Field(default=None)
    path_local: str | None = Field(default=None)
    sha: str
    size_bytes: int
