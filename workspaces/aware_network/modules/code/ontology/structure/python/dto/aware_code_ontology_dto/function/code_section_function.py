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
    from aware_code_ontology_dto.code.code_section import CodeSection
    from aware_code_ontology_dto.comment.code_section_comment import CodeSectionComment
    from aware_code_ontology_dto.decorator.code_section_decorator import CodeSectionDecorator
    from aware_code_ontology_dto.function.code_section_function_attribute import CodeSectionFunctionAttribute
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionFunction(BaseModel):
    # Relationships
    name_segment: ContentPartTextSegment | None = Field(default=None)
    body_segment: ContentPartTextSegment | None = Field(default=None)
    signature_segment: ContentPartTextSegment
    return_type_segment: ContentPartTextSegment | None = Field(default=None)
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    code_section_decorators: list[CodeSectionDecorator] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_function")

    # Attributes
    name: str
    description: str | None = Field(default=None)
    is_async: bool
    is_public: bool
    is_static: bool = Field(default=False)
    is_classmethod: bool = Field(default=False)
    verb: str | None = Field(default=None)
