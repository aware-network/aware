from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code_section import CodeSection
    from aware_code_ontology_orm_models.decorator.code_section_decorator_expression import (
        CodeSectionDecoratorExpression,
    )
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionDecorator(ORMModel):
    # Relationships
    code_section_decorator_expressions: list[CodeSectionDecoratorExpression] = Field(default_factory=list)
    name_segment: ContentPartTextSegment
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_decorator")

    # Foreign Keys
    code_section_class_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionClass.code_section_decorators"
    )
    code_section_function_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionFunction.code_section_decorators"
    )
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_decorator")
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionDecorator.name_segment")
