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
    from aware_code_ontology.code.code_section import CodeSection
    from aware_code_ontology.comment.code_section_comment import CodeSectionComment
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionAttribute(ORMModel):
    # Relationships
    name_segment: ContentPartTextSegment | None = Field(default=None)
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    default_value_segment: ContentPartTextSegment | None = Field(default=None)
    type_segment: ContentPartTextSegment | None = Field(default=None)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_attribute")

    # Attributes
    name: str
    description: str | None = Field(default=None)
    type_text: str | None = Field(default=None)
    default_value_text: str | None = Field(default=None)
    is_required: bool
    is_public: bool
    is_unique: bool
    is_primary: bool
    is_many_to_many: bool = Field(default=False)
    edge_spec_name: str | None = Field(default=None)

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_attribute")
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionAttribute.name_segment")
    default_value_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionAttribute.default_value_segment"
    )
    type_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionAttribute.type_segment")

    @classmethod
    async def build_via_code_section(cls, code_section_id: UUID) -> CodeSectionAttribute:
        """Build the attribute payload under a CodeSection."""

        payload = {"code_section_id": code_section_id}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionAttribute):
            return value
        return CodeSectionAttribute.validate_invocation_value(value)


class CodeSectionAttributeBuildViaCodeSectionInput(BaseModel):
    code_section_id: UUID = Field(description="Foreign key for CodeSection.code_section_attribute")


class CodeSectionAttributeBuildViaCodeSectionOutput(BaseModel):
    value: CodeSectionAttribute


FUNCTIONS = {
    "CodeSectionAttribute": {
        "build_via_code_section": {
            "canonical": {
                "name": "build_via_code_section",
                "description": "Build the attribute payload under a CodeSection.",
                "is_constructor": True,
            },
            "input": CodeSectionAttributeBuildViaCodeSectionInput,
            "output": CodeSectionAttributeBuildViaCodeSectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionAttribute",
    "CodeSectionAttributeBuildViaCodeSectionInput",
    "CodeSectionAttributeBuildViaCodeSectionOutput",
    "FUNCTIONS",
]
