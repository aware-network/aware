from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Content Ontology Dto
from aware_content_ontology_dto.content.content_enums import ModalityType

if TYPE_CHECKING:
    from aware_storage_ontology_dto.blob.storage_blob import StorageBlob


class ContentPartFile(BaseModel):
    # Relationships
    storage_blob: StorageBlob | None = Field(default=None, description="Association target reference to StorageBlob")

    # Attributes
    inline_data: bytes | None = Field(default=None)
    mime_type: str
    modality_type: ModalityType
    provider_id: str | None = Field(default=None)
    raw_path: str | None = Field(default=None)
