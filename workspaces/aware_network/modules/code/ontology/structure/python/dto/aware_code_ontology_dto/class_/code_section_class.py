from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.attribute.code_section_attribute import CodeSectionAttribute
    from aware_code_ontology_dto.class_.code_section_class_attribute import CodeSectionClassAttribute
    from aware_code_ontology_dto.class_.code_section_class_base import CodeSectionClassBase
    from aware_code_ontology_dto.class_.code_section_class_function import CodeSectionClassFunction
    from aware_code_ontology_dto.code.code_section import CodeSection
    from aware_code_ontology_dto.comment.code_section_comment import CodeSectionComment
    from aware_code_ontology_dto.decorator.code_section_decorator import CodeSectionDecorator
    from aware_code_ontology_dto.function.code_section_function import CodeSectionFunction
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionClass(BaseModel):
    # Relationships
    code_section_class_bases: list[CodeSectionClassBase] = Field(default_factory=list)
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    code_section_decorators: list[CodeSectionDecorator] = Field(default_factory=list)
    name_segment: ContentPartTextSegment
    keyword_segment: ContentPartTextSegment | None = Field(default=None)
    modifiers_segment: ContentPartTextSegment | None = Field(default=None)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_class")

    # Attributes
    name: str
    description: str | None = Field(default=None)
    verb: str | None = Field(default=None)
    verb_target: str | None = Field(default=None)
    is_edge: bool = Field(default=False)
    is_inline_value: bool = Field(default=False)
