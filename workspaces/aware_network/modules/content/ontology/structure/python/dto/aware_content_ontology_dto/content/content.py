from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Content Ontology Dto
from aware_content_ontology_dto.content.content_enums import ContentSource

if TYPE_CHECKING:
    from aware_content_ontology_dto.content.content_index import ContentIndex
    from aware_content_ontology_dto.content.content_layout import ContentLayout
    from aware_content_ontology_dto.part.content_part_content import ContentPartContent


class Content(BaseModel):
    # Relationships
    content_index: ContentIndex | None = Field(default=None)
    content_layouts: list[ContentLayout] = Field(default_factory=list)
    content_part_contents: list[ContentPartContent] = Field(default_factory=list)

    # Attributes
    key: str
    title: str | None = Field(default=None)
    source: ContentSource
    token_count: int | None = Field(default=None)
