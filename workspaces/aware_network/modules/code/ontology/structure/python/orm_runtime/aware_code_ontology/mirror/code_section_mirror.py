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
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionMirror(ORMModel):
    """
    Canonical mirror directive (API transport allowlist).
    Mirrors are explicit, file-level statements that mark which ontology symbols
    are copied into an API OCG for DTO materialization.
    """

    # Relationships
    target_segment: ContentPartTextSegment
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_mirror")

    # Attributes
    target_text: str

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_mirror")
    target_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionMirror.target_segment")

    @classmethod
    async def build_via_code_section(cls, code_section_id: UUID) -> CodeSectionMirror:
        """Build the mirror payload under a CodeSection."""

        payload = {"code_section_id": code_section_id}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionMirror):
            return value
        return CodeSectionMirror.validate_invocation_value(value)


class CodeSectionMirrorBuildViaCodeSectionInput(BaseModel):
    code_section_id: UUID = Field(description="Foreign key for CodeSection.code_section_mirror")


class CodeSectionMirrorBuildViaCodeSectionOutput(BaseModel):
    value: CodeSectionMirror


FUNCTIONS = {
    "CodeSectionMirror": {
        "build_via_code_section": {
            "canonical": {
                "name": "build_via_code_section",
                "description": "Build the mirror payload under a CodeSection.",
                "is_constructor": True,
            },
            "input": CodeSectionMirrorBuildViaCodeSectionInput,
            "output": CodeSectionMirrorBuildViaCodeSectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionMirror",
    "CodeSectionMirrorBuildViaCodeSectionInput",
    "CodeSectionMirrorBuildViaCodeSectionOutput",
    "FUNCTIONS",
]
