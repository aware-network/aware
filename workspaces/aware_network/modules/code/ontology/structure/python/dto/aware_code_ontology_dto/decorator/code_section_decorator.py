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
    from aware_code_ontology_dto.decorator.code_section_decorator_expression import CodeSectionDecoratorExpression
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionDecorator(BaseModel):
    # Relationships
    code_section_decorator_expressions: list[CodeSectionDecoratorExpression] = Field(default_factory=list)
    name_segment: ContentPartTextSegment
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_decorator")
