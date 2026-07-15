from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code_section import CodeSection
    from aware_code_ontology_dto.comment.code_section_comment import CodeSectionComment
    from aware_code_ontology_dto.enum.code_section_enum_value import CodeSectionEnumValue
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionEnum(BaseModel):
    # Relationships
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    name_segment: ContentPartTextSegment
    code_section_enum_values: list[CodeSectionEnumValue] = Field(default_factory=list)
    content_part_text_segments: list[ContentPartTextSegment] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_enum")

    # Attributes
    name: str
    description: str | None = Field(default=None)
