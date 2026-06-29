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
    from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
    from aware_code_ontology.code.code_section import CodeSection
    from aware_code_ontology.comment.code_section_comment import CodeSectionComment
    from aware_code_ontology.decorator.code_section_decorator import CodeSectionDecorator
    from aware_code_ontology.function.code_section_function_attribute import CodeSectionFunctionAttribute
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionFunction(ORMModel):
    # Relationships
    name_segment: ContentPartTextSegment | None = Field(default=None)
    body_segment: ContentPartTextSegment | None = Field(default=None)
    signature_segment: ContentPartTextSegment
    return_type_segment: ContentPartTextSegment | None = Field(default=None)
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    code_section_decorators: list[CodeSectionDecorator] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_function")

    # Attributes
    name: str
    description: str | None = Field(default=None)
    is_async: bool
    is_public: bool
    is_static: bool = Field(default=False)
    is_classmethod: bool = Field(default=False)
    verb: str | None = Field(default=None)

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_function")
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionFunction.name_segment")
    body_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionFunction.body_segment")
    signature_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionFunction.signature_segment"
    )
    return_type_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionFunction.return_type_segment"
    )

    # Edges
    code_section_function_attributes: list[CodeSectionFunctionAttribute] = Field(
        default_factory=list, exclude=True, description="Edge association helper for code_section_attributes"
    )

    @property
    def code_section_attributes(self) -> list[CodeSectionAttribute]:
        return [
            edge.code_section_attribute
            for edge in self.code_section_function_attributes
            if edge.code_section_attribute is not None
        ]

    @classmethod
    async def build_via_code_section(cls, code_section_id: UUID) -> CodeSectionFunction:
        """Build the function payload under a CodeSection."""

        payload = {"code_section_id": code_section_id}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionFunction):
            return value
        return CodeSectionFunction.validate_invocation_value(value)


class CodeSectionFunctionBuildViaCodeSectionInput(BaseModel):
    code_section_id: UUID = Field(description="Foreign key for CodeSection.code_section_function")


class CodeSectionFunctionBuildViaCodeSectionOutput(BaseModel):
    value: CodeSectionFunction


FUNCTIONS = {
    "CodeSectionFunction": {
        "build_via_code_section": {
            "canonical": {
                "name": "build_via_code_section",
                "description": "Build the function payload under a CodeSection.",
                "is_constructor": True,
            },
            "input": CodeSectionFunctionBuildViaCodeSectionInput,
            "output": CodeSectionFunctionBuildViaCodeSectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionFunction",
    "CodeSectionFunctionBuildViaCodeSectionInput",
    "CodeSectionFunctionBuildViaCodeSectionOutput",
    "FUNCTIONS",
]
