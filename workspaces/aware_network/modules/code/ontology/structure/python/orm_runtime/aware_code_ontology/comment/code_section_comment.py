from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.comment.code_section_comment_enums import CodeSectionCommentType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_code_ontology.code.code_section import CodeSection
    from aware_code_ontology.comment.code_section_comment_content import CodeSectionCommentContent


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

    async def create_content(self, position: int) -> CodeSectionCommentContent:
        """Create an ordered comment-content item under this comment."""

        payload = {"position": position}
        result = await invoke_instance(orm_model=self, function_name="create_content", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.comment.code_section_comment_content import CodeSectionCommentContent

        if isinstance(value, CodeSectionCommentContent):
            return value
        return CodeSectionCommentContent.validate_invocation_value(value)

    @classmethod
    async def build_via_code_section(cls, code_section_id: UUID, type: CodeSectionCommentType) -> CodeSectionComment:
        """Build the comment payload under a CodeSection."""

        payload = {"code_section_id": code_section_id, "type": type}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionComment):
            return value
        return CodeSectionComment.validate_invocation_value(value)


class CodeSectionCommentCreateContentInput(BaseModel):
    position: int


class CodeSectionCommentCreateContentOutput(BaseModel):
    value: CodeSectionCommentContent


class CodeSectionCommentBuildViaCodeSectionInput(BaseModel):
    code_section_id: UUID = Field(description="Foreign key for CodeSection.code_section_comment")
    type: CodeSectionCommentType


class CodeSectionCommentBuildViaCodeSectionOutput(BaseModel):
    value: CodeSectionComment


FUNCTIONS = {
    "CodeSectionComment": {
        "create_content": {
            "canonical": {
                "name": "create_content",
                "description": "Create an ordered comment-content item under this comment.",
                "is_constructor": False,
            },
            "input": CodeSectionCommentCreateContentInput,
            "output": CodeSectionCommentCreateContentOutput,
        },
        "build_via_code_section": {
            "canonical": {
                "name": "build_via_code_section",
                "description": "Build the comment payload under a CodeSection.",
                "is_constructor": True,
            },
            "input": CodeSectionCommentBuildViaCodeSectionInput,
            "output": CodeSectionCommentBuildViaCodeSectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionComment",
    "CodeSectionCommentCreateContentInput",
    "CodeSectionCommentCreateContentOutput",
    "CodeSectionCommentBuildViaCodeSectionInput",
    "CodeSectionCommentBuildViaCodeSectionOutput",
    "FUNCTIONS",
]
