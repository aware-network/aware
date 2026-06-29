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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_code_ontology.code.code_section import CodeSection
    from aware_code_ontology.decorator.code_section_decorator_expression import CodeSectionDecoratorExpression
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


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

    async def create_expression(self, position: int) -> CodeSectionDecoratorExpression:
        """Create an ordered decorator-expression entry under this decorator."""

        payload = {"position": position}
        result = await invoke_instance(orm_model=self, function_name="create_expression", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.decorator.code_section_decorator_expression import CodeSectionDecoratorExpression

        if isinstance(value, CodeSectionDecoratorExpression):
            return value
        return CodeSectionDecoratorExpression.validate_invocation_value(value)

    @classmethod
    async def build_via_code_section(cls, code_section_id: UUID) -> CodeSectionDecorator:
        """Build the decorator payload under a CodeSection."""

        payload = {"code_section_id": code_section_id}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionDecorator):
            return value
        return CodeSectionDecorator.validate_invocation_value(value)


class CodeSectionDecoratorCreateExpressionInput(BaseModel):
    position: int


class CodeSectionDecoratorCreateExpressionOutput(BaseModel):
    value: CodeSectionDecoratorExpression


class CodeSectionDecoratorBuildViaCodeSectionInput(BaseModel):
    code_section_id: UUID = Field(description="Foreign key for CodeSection.code_section_decorator")


class CodeSectionDecoratorBuildViaCodeSectionOutput(BaseModel):
    value: CodeSectionDecorator


FUNCTIONS = {
    "CodeSectionDecorator": {
        "create_expression": {
            "canonical": {
                "name": "create_expression",
                "description": "Create an ordered decorator-expression entry under this decorator.",
                "is_constructor": False,
            },
            "input": CodeSectionDecoratorCreateExpressionInput,
            "output": CodeSectionDecoratorCreateExpressionOutput,
        },
        "build_via_code_section": {
            "canonical": {
                "name": "build_via_code_section",
                "description": "Build the decorator payload under a CodeSection.",
                "is_constructor": True,
            },
            "input": CodeSectionDecoratorBuildViaCodeSectionInput,
            "output": CodeSectionDecoratorBuildViaCodeSectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionDecorator",
    "CodeSectionDecoratorCreateExpressionInput",
    "CodeSectionDecoratorCreateExpressionOutput",
    "CodeSectionDecoratorBuildViaCodeSectionInput",
    "CodeSectionDecoratorBuildViaCodeSectionOutput",
    "FUNCTIONS",
]
