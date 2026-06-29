from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.expression.code_section_expression_enums import CodeSectionExpressionType

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code_section import CodeSection
    from aware_code_ontology_dto.comment.code_section_comment import CodeSectionComment
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionExpression(BaseModel):
    # Relationships
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    value_segment: ContentPartTextSegment
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_expression")

    # Attributes
    type: CodeSectionExpressionType
