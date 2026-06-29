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
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionClassBase(ORMModel):
    # Relationships
    segment: ContentPartTextSegment | None = Field(default=None)

    # Attributes
    base_ref: str
    is_augment: bool = Field(default=False)

    # Foreign Keys
    code_section_class_id: UUID = Field(description="Foreign key for CodeSectionClass.code_section_class_bases")
    segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionClassBase.segment")

    @classmethod
    async def build_via_code_section_class(
        cls, code_section_class_id: UUID, base_ref: str, is_augment: bool = False
    ) -> CodeSectionClassBase:
        """Build a deterministic class-base entry under a class section."""

        payload = {"code_section_class_id": code_section_class_id, "base_ref": base_ref, "is_augment": is_augment}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section_class", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionClassBase):
            return value
        return CodeSectionClassBase.validate_invocation_value(value)


class CodeSectionClassBaseBuildViaCodeSectionClassInput(BaseModel):
    code_section_class_id: UUID = Field(description="Foreign key for CodeSectionClass.code_section_class_bases")
    base_ref: str
    is_augment: bool = Field(default=False)


class CodeSectionClassBaseBuildViaCodeSectionClassOutput(BaseModel):
    value: CodeSectionClassBase


FUNCTIONS = {
    "CodeSectionClassBase": {
        "build_via_code_section_class": {
            "canonical": {
                "name": "build_via_code_section_class",
                "description": "Build a deterministic class-base entry under a class section.",
                "is_constructor": True,
            },
            "input": CodeSectionClassBaseBuildViaCodeSectionClassInput,
            "output": CodeSectionClassBaseBuildViaCodeSectionClassOutput,
        },
    },
}

__all__ = [
    "CodeSectionClassBase",
    "CodeSectionClassBaseBuildViaCodeSectionClassInput",
    "CodeSectionClassBaseBuildViaCodeSectionClassOutput",
    "FUNCTIONS",
]
