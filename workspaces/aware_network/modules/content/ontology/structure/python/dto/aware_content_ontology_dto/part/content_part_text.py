from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_content_ontology_dto.part.content_part_text_index import ContentPartTextIndex
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment
    from aware_storage_ontology_dto.blob.storage_blob import StorageBlob


class ContentPartText(BaseModel):
    # Relationships
    blob: StorageBlob | None = Field(default=None)
    index: ContentPartTextIndex | None = Field(default=None)
    segments: list[ContentPartTextSegment] = Field(default_factory=list)

    # Attributes
    key: str = Field(default="default")
    inline_text: str | None = Field(default=None)
