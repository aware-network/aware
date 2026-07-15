from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Content Ontology Orm Models
from aware_content_ontology_orm_models.content.content_enums import ModalityType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_storage_ontology_orm_models.blob.storage_blob import StorageBlob


class ContentPartFile(ORMModel):
    # Relationships
    storage_blob: StorageBlob | None = Field(
        default=None, exclude=True, description="Association target reference to StorageBlob"
    )

    # Attributes
    inline_data: bytes | None = Field(default=None)
    mime_type: str
    modality_type: ModalityType
    provider_id: str | None = Field(default=None)
    raw_path: str | None = Field(default=None)

    # Foreign Keys
    storage_blob_id: UUID = Field(description="Join FK to StorageBlob")
    content_part_id: UUID = Field(description="Join FK to ContentPart")
