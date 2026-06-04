from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Storage Ontology Dto
from aware_storage_ontology_dto.bucket.storage_bucket_enums import StorageBackend

# Types
from aware_types import JsonObject


class StorageBucket(BaseModel):
    # Attributes
    allowed_mime_types: list[str] = Field(default_factory=list)
    backend: StorageBackend = Field(default=StorageBackend.local)
    config: JsonObject | None = Field(default=None)
    name: str
