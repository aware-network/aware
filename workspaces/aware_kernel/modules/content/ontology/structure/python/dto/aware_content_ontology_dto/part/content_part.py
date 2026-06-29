from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Content Ontology Dto
from aware_content_ontology_dto.part.content_part_enums import ContentPartType

if TYPE_CHECKING:
    from aware_content_ontology_dto.part.content_part_file import ContentPartFile
    from aware_content_ontology_dto.part.content_part_multimodal_index import ContentPartMultimodalIndex
    from aware_content_ontology_dto.part.content_part_text import ContentPartText
    from aware_storage_ontology_dto.blob.storage_blob import StorageBlob


class ContentPart(BaseModel):
    # Relationships
    content_part_multimodal_index: ContentPartMultimodalIndex | None = Field(default=None)
    content_part_text: ContentPartText | None = Field(default=None)

    # Attributes
    type: ContentPartType
