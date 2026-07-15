from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_code_ontology.expression.code_section_expression import CodeSectionExpression
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


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

    @classmethod
    async def build_via_code_section_decorator(
        cls, code_section_decorator_id: UUID, position: int = 0
    ) -> CodeSectionDecoratorExpression:
        """Build an ordered decorator-expression entry under a decorator."""

        payload = {"code_section_decorator_id": code_section_decorator_id, "position": position}
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_code_section_decorator", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionDecoratorExpression):
            return value
        return CodeSectionDecoratorExpression.validate_invocation_value(value)


class CodeSectionDecoratorExpressionBuildViaCodeSectionDecoratorInput(BaseModel):
    code_section_decorator_id: UUID = Field(
        description="Foreign key for CodeSectionDecorator.code_section_decorator_expressions"
    )
    position: int = Field(default=0)


class CodeSectionDecoratorExpressionBuildViaCodeSectionDecoratorOutput(BaseModel):
    value: CodeSectionDecoratorExpression


FUNCTIONS = {
    "CodeSectionDecoratorExpression": {
        "build_via_code_section_decorator": {
            "canonical": {
                "name": "build_via_code_section_decorator",
                "description": "Build an ordered decorator-expression entry under a decorator.",
                "is_constructor": True,
            },
            "input": CodeSectionDecoratorExpressionBuildViaCodeSectionDecoratorInput,
            "output": CodeSectionDecoratorExpressionBuildViaCodeSectionDecoratorOutput,
        },
    },
}

__all__ = [
    "CodeSectionDecoratorExpression",
    "CodeSectionDecoratorExpressionBuildViaCodeSectionDecoratorInput",
    "CodeSectionDecoratorExpressionBuildViaCodeSectionDecoratorOutput",
    "FUNCTIONS",
]
