from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Content Ontology Orm Models
from aware_content_ontology_orm_models.part.content_part_enums import ContentPartType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.part.content_part_file import ContentPartFile
    from aware_content_ontology_orm_models.part.content_part_multimodal_index import ContentPartMultimodalIndex
    from aware_content_ontology_orm_models.part.content_part_text import ContentPartText
    from aware_storage_ontology_orm_models.blob.storage_blob import StorageBlob


class ContentPart(ORMModel):
    # Relationships
    content_part_multimodal_index: ContentPartMultimodalIndex | None = Field(default=None)
    content_part_text: ContentPartText | None = Field(default=None)

    # Attributes
    type: ContentPartType

    # Foreign Keys
    content_part_content_id: UUID = Field(description="Foreign key for ContentPartContent.content_part")

    # Edges
    content_part_file: ContentPartFile | None = Field(
        default=None, exclude=True, description="Edge association helper for storage_blobs"
    )

    @property
    def storage_blobs(self) -> StorageBlob | None:
        return (
            self.content_part_file.storage_blob
            if self.content_part_file is not None and self.content_part_file.storage_blob is not None
            else None
        )
