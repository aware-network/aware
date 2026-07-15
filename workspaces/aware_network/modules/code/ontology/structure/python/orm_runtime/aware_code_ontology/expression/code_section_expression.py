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
from aware_code_ontology.expression.code_section_expression_enums import CodeSectionExpressionType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_code_ontology.code.code_section import CodeSection
    from aware_code_ontology.comment.code_section_comment import CodeSectionComment
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


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

    @classmethod
    async def build_via_code_section(
        cls, code_section_id: UUID, type: CodeSectionExpressionType
    ) -> CodeSectionExpression:
        """Build the expression payload under a CodeSection."""

        payload = {"code_section_id": code_section_id, "type": type}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionExpression):
            return value
        return CodeSectionExpression.validate_invocation_value(value)


class CodeSectionExpressionBuildViaCodeSectionInput(BaseModel):
    code_section_id: UUID = Field(description="Foreign key for CodeSection.code_section_expression")
    type: CodeSectionExpressionType


class CodeSectionExpressionBuildViaCodeSectionOutput(BaseModel):
    value: CodeSectionExpression


FUNCTIONS = {
    "CodeSectionExpression": {
        "build_via_code_section": {
            "canonical": {
                "name": "build_via_code_section",
                "description": "Build the expression payload under a CodeSection.",
                "is_constructor": True,
            },
            "input": CodeSectionExpressionBuildViaCodeSectionInput,
            "output": CodeSectionExpressionBuildViaCodeSectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionExpression",
    "CodeSectionExpressionBuildViaCodeSectionInput",
    "CodeSectionExpressionBuildViaCodeSectionOutput",
    "FUNCTIONS",
]
