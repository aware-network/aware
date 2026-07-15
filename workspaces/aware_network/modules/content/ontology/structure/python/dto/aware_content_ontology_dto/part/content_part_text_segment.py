from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_content_ontology_dto.part.content_part_text import ContentPartText
    from aware_content_ontology_dto.part.content_part_text_segment_translation import ContentPartTextSegmentTranslation
    from aware_content_ontology_dto.part.content_part_text_style import ContentPartTextStyle


class ContentPartTextSegment(BaseModel):
    # Relationships
    content_part_text_segment_translations: list[ContentPartTextSegmentTranslation] = Field(default_factory=list)
    parent: ContentPartTextSegment | None = Field(default=None)
    style: ContentPartTextStyle | None = Field(default=None)
    content_part_text: ContentPartText = Field(description="Reverse view for ContentPartText.segments")

    # Attributes
    key: str = Field(default="default")
    byte_end: int | None = Field(default=None)
    byte_start: int | None = Field(default=None)
