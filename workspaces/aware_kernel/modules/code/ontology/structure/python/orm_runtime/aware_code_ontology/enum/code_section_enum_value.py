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


class CodeSectionEnumValue(ORMModel):
    # Relationships
    value_segment: ContentPartTextSegment
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_enum_value")

    # Attributes
    value: str
    description: str | None = Field(default=None)
    position: int = Field(default=0)

    # Foreign Keys
    code_section_enum_id: UUID = Field(description="Foreign key for CodeSectionEnum.code_section_enum_values")
    code_section_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSection.code_section_enum_value"
    )
    value_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionEnumValue.value_segment"
    )

    @classmethod
    async def build_via_code_section(cls, code_section_id: UUID, value: str, position: int = 0) -> CodeSectionEnumValue:
        """Build the enum-value payload under a CodeSection."""

        payload = {"code_section_id": code_section_id, "value": value, "position": position}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionEnumValue):
            return value
        return CodeSectionEnumValue.validate_invocation_value(value)


class CodeSectionEnumValueBuildViaCodeSectionInput(BaseModel):
    code_section_id: UUID = Field(description="Foreign key for CodeSection.code_section_enum_value")
    value: str
    position: int = Field(default=0)


class CodeSectionEnumValueBuildViaCodeSectionOutput(BaseModel):
    value: CodeSectionEnumValue


FUNCTIONS = {
    "CodeSectionEnumValue": {
        "build_via_code_section": {
            "canonical": {
                "name": "build_via_code_section",
                "description": "Build the enum-value payload under a CodeSection.",
                "is_constructor": True,
            },
            "input": CodeSectionEnumValueBuildViaCodeSectionInput,
            "output": CodeSectionEnumValueBuildViaCodeSectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionEnumValue",
    "CodeSectionEnumValueBuildViaCodeSectionInput",
    "CodeSectionEnumValueBuildViaCodeSectionOutput",
    "FUNCTIONS",
]
