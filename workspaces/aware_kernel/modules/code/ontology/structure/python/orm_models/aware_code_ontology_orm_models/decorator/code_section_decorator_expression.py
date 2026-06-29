from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.expression.code_section_expression import CodeSectionExpression
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionDecoratorExpression(ORMModel):
    # Relationships
    code_section_expression: CodeSectionExpression
    name_segment: ContentPartTextSegment | None = Field(default=None)

    # Attributes
    position: int = Field(default=0)

    # Foreign Keys
    code_section_decorator_id: UUID = Field(
        description="Foreign key for CodeSectionDecorator.code_section_decorator_expressions"
    )
    code_section_expression_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionDecoratorExpression.code_section_expression"
    )
    name_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionDecoratorExpression.name_segment"
    )
