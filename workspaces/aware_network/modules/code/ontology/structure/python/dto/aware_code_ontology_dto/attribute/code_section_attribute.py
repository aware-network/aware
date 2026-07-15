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
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionAttribute(BaseModel):
    # Relationships
    name_segment: ContentPartTextSegment | None = Field(default=None)
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    default_value_segment: ContentPartTextSegment | None = Field(default=None)
    type_segment: ContentPartTextSegment | None = Field(default=None)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_attribute")

    # Attributes
    name: str
    description: str | None = Field(default=None)
    type_text: str | None = Field(default=None)
    default_value_text: str | None = Field(default=None)
    is_required: bool
    is_public: bool
    is_unique: bool
    is_primary: bool
    is_many_to_many: bool = Field(default=False)
    edge_spec_name: str | None = Field(default=None)
