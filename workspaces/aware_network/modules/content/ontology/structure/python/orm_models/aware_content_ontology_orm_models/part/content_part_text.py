from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.part.content_part_text_index import ContentPartTextIndex
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment
    from aware_storage_ontology_orm_models.blob.storage_blob import StorageBlob


class ContentPartText(ORMModel):
    # Relationships
    blob: StorageBlob | None = Field(default=None, exclude=True)
    index: ContentPartTextIndex | None = Field(default=None, exclude=True)
    segments: list[ContentPartTextSegment] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str = Field(default="default")
    inline_text: str | None = Field(default=None)

    # Foreign Keys
    content_part_id: UUID | None = Field(default=None, description="Foreign key for ContentPart.content_part_text")
    blob_id: UUID | None = Field(default=None, description="Foreign key for ContentPartText.blob")
