from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.expression.code_section_expression import CodeSectionExpression
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionDecoratorExpression(BaseModel):
    # Relationships
    code_section_expression: CodeSectionExpression
    name_segment: ContentPartTextSegment | None = Field(default=None)

    # Attributes
    position: int = Field(default=0)
