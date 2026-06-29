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


class CodeSectionImportName(BaseModel):
    # Relationships
    name_segment: ContentPartTextSegment
    alias_segment: ContentPartTextSegment | None = Field(default=None)

    # Attributes
    name_text: str
    alias_text: str | None = Field(default=None)
