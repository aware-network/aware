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
    from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
    from aware_code_ontology.class_.code_section_class_attribute import CodeSectionClassAttribute
    from aware_code_ontology.class_.code_section_class_base import CodeSectionClassBase
    from aware_code_ontology.class_.code_section_class_function import CodeSectionClassFunction
    from aware_code_ontology.code.code_section import CodeSection
    from aware_code_ontology.comment.code_section_comment import CodeSectionComment
    from aware_code_ontology.decorator.code_section_decorator import CodeSectionDecorator
    from aware_code_ontology.function.code_section_function import CodeSectionFunction
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionClass(ORMModel):
    # Relationships
    code_section_class_bases: list[CodeSectionClassBase] = Field(default_factory=list)
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    code_section_decorators: list[CodeSectionDecorator] = Field(default_factory=list)
    name_segment: ContentPartTextSegment
    keyword_segment: ContentPartTextSegment | None = Field(default=None)
    modifiers_segment: ContentPartTextSegment | None = Field(default=None)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_class")

    # Attributes
    name: str
    description: str | None = Field(default=None)
    verb: str | None = Field(default=None)
    verb_target: str | None = Field(default=None)
    is_edge: bool = Field(default=False)
    is_inline_value: bool = Field(default=False)

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_class")
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionClass.name_segment")
    keyword_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionClass.keyword_segment"
    )
    modifiers_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionClass.modifiers_segment"
    )

    # Edges
    code_section_class_attributes: list[CodeSectionClassAttribute] = Field(
        default_factory=list, exclude=True, description="Edge association helper for code_section_attributes"
    )
    code_section_class_functions: list[CodeSectionClassFunction] = Field(
        default_factory=list, exclude=True, description="Edge association helper for code_section_functions"
    )

    @property
    def code_section_attributes(self) -> list[CodeSectionAttribute]:
        return [
            edge.code_section_attribute
            for edge in self.code_section_class_attributes
            if edge.code_section_attribute is not None
        ]

    @property
    def code_section_functions(self) -> list[CodeSectionFunction]:
        return [
            edge.code_section_function
            for edge in self.code_section_class_functions
            if edge.code_section_function is not None
        ]

    async def create_base(self, base_ref: str, is_augment: bool = False) -> CodeSectionClassBase:
        """Create a deterministic base entry under this class."""

        payload = {"base_ref": base_ref, "is_augment": is_augment}
        result = await invoke_instance(orm_model=self, function_name="create_base", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.class_.code_section_class_base import CodeSectionClassBase

        if isinstance(value, CodeSectionClassBase):
            return value
        return CodeSectionClassBase.validate_invocation_value(value)

    @classmethod
    async def build_via_code_section(cls, code_section_id: UUID) -> CodeSectionClass:
        """Build the class payload under a CodeSection."""

        payload = {"code_section_id": code_section_id}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionClass):
            return value
        return CodeSectionClass.validate_invocation_value(value)


class CodeSectionClassCreateBaseInput(BaseModel):
    base_ref: str
    is_augment: bool = Field(default=False)


class CodeSectionClassCreateBaseOutput(BaseModel):
    value: CodeSectionClassBase


class CodeSectionClassBuildViaCodeSectionInput(BaseModel):
    code_section_id: UUID = Field(description="Foreign key for CodeSection.code_section_class")


class CodeSectionClassBuildViaCodeSectionOutput(BaseModel):
    value: CodeSectionClass


FUNCTIONS = {
    "CodeSectionClass": {
        "create_base": {
            "canonical": {
                "name": "create_base",
                "description": "Create a deterministic base entry under this class.",
                "is_constructor": False,
            },
            "input": CodeSectionClassCreateBaseInput,
            "output": CodeSectionClassCreateBaseOutput,
        },
        "build_via_code_section": {
            "canonical": {
                "name": "build_via_code_section",
                "description": "Build the class payload under a CodeSection.",
                "is_constructor": True,
            },
            "input": CodeSectionClassBuildViaCodeSectionInput,
            "output": CodeSectionClassBuildViaCodeSectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionClass",
    "CodeSectionClassCreateBaseInput",
    "CodeSectionClassCreateBaseOutput",
    "CodeSectionClassBuildViaCodeSectionInput",
    "CodeSectionClassBuildViaCodeSectionOutput",
    "FUNCTIONS",
]
