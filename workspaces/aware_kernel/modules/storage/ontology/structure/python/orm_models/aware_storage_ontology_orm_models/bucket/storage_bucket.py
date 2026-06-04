from __future__ import annotations

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Storage Ontology Orm Models
from aware_storage_ontology_orm_models.bucket.storage_bucket_enums import StorageBackend

# Types
from aware_types import JsonObject


class StorageBucket(ORMModel):
    # Attributes
    allowed_mime_types: list[str] = Field(default_factory=list)
    backend: StorageBackend = Field(default=StorageBackend.local)
    config: JsonObject | None = Field(default=None)
    name: str
