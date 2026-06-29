from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.expression.code_section_expression_enums import CodeSectionExpressionType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code_section import CodeSection
    from aware_code_ontology_orm_models.comment.code_section_comment import CodeSectionComment
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionExpression(ORMModel):
    # Relationships
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    value_segment: ContentPartTextSegment
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_expression")

    # Attributes
    type: CodeSectionExpressionType

    # Foreign Keys
    code_section_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSection.code_section_expression"
    )
    value_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionExpression.value_segment"
    )
