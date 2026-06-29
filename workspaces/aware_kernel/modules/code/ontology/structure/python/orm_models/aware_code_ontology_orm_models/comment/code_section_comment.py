from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.comment.code_section_comment_enums import CodeSectionCommentType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code_section import CodeSection
    from aware_code_ontology_orm_models.comment.code_section_comment_content import CodeSectionCommentContent


class CodeSectionComment(ORMModel):
    # Relationships
    code_section_comment_contents: list[CodeSectionCommentContent] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_comment")

    # Attributes
    type: CodeSectionCommentType

    # Foreign Keys
    code_section_enum_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionEnum.code_section_comments"
    )
    code_section_expression_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionExpression.code_section_comments"
    )
    code_section_projection_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionProjection.code_section_comments"
    )
    code_section_attribute_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionAttribute.code_section_comments"
    )
    code_section_enum_value_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionEnumValue.code_section_comments"
    )
    code_section_class_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionClass.code_section_comments"
    )
    code_section_function_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionFunction.code_section_comments"
    )
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_comment")
