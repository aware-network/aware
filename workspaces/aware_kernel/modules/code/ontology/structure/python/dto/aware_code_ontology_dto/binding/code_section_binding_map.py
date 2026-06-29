from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionBindingMap(BaseModel):
    # Relationships
    name_segment: ContentPartTextSegment
    source_segment: ContentPartTextSegment
    target_segment: ContentPartTextSegment
    body_segment: ContentPartTextSegment | None = Field(default=None)
    template_segment: ContentPartTextSegment | None = Field(default=None)

    # Attributes
    name: str
    source_ref: str
    target_ref: str
    description: str | None = Field(default=None)
    template_text: str | None = Field(default=None)
