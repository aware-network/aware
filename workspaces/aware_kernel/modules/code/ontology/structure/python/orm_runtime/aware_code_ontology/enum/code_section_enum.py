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
    from aware_code_ontology.enum.code_section_enum_value import CodeSectionEnumValue
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionEnum(ORMModel):
    # Relationships
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    name_segment: ContentPartTextSegment
    code_section_enum_values: list[CodeSectionEnumValue] = Field(default_factory=list)
    content_part_text_segments: list[ContentPartTextSegment] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_enum")

    # Attributes
    name: str
    description: str | None = Field(default=None)

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_enum")
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionEnum.name_segment")

    @classmethod
    async def build_via_code_section(cls, code_section_id: UUID) -> CodeSectionEnum:
        """Build the enum payload under a CodeSection."""

        payload = {"code_section_id": code_section_id}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionEnum):
            return value
        return CodeSectionEnum.validate_invocation_value(value)


class CodeSectionEnumBuildViaCodeSectionInput(BaseModel):
    code_section_id: UUID = Field(description="Foreign key for CodeSection.code_section_enum")


class CodeSectionEnumBuildViaCodeSectionOutput(BaseModel):
    value: CodeSectionEnum


FUNCTIONS = {
    "CodeSectionEnum": {
        "build_via_code_section": {
            "canonical": {
                "name": "build_via_code_section",
                "description": "Build the enum payload under a CodeSection.",
                "is_constructor": True,
            },
            "input": CodeSectionEnumBuildViaCodeSectionInput,
            "output": CodeSectionEnumBuildViaCodeSectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionEnum",
    "CodeSectionEnumBuildViaCodeSectionInput",
    "CodeSectionEnumBuildViaCodeSectionOutput",
    "FUNCTIONS",
]
