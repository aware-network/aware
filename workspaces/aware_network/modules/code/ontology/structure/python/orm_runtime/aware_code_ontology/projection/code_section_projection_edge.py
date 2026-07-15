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


class CodeSectionProjectionEdge(ORMModel):
    # Relationships
    type_segment: ContentPartTextSegment
    member_segment: ContentPartTextSegment
    target_segment: ContentPartTextSegment | None = Field(default=None)

    # Attributes
    type_ref: str
    member: str
    target_projection_ref: str | None = Field(
        default=None,
        description="Optional portal target projection reference.\nForms:\n- unqualified: `Focus`\n- qualified: `aware_identity.Identity` (recommended for cross-package)",
    )

    # Foreign Keys
    code_section_projection_id: UUID = Field(description="Foreign key for CodeSectionProjection.projection_edges")
    type_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionProjectionEdge.type_segment"
    )
    member_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionProjectionEdge.member_segment"
    )
    target_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionProjectionEdge.target_segment"
    )

    @classmethod
    async def build_via_code_section_projection(
        cls, code_section_projection_id: UUID, member: str, type_ref: str, target_projection_ref: str | None = None
    ) -> CodeSectionProjectionEdge:
        """Build a deterministic projection-edge entry under a projection."""

        payload = {
            "code_section_projection_id": code_section_projection_id,
            "member": member,
            "type_ref": type_ref,
            "target_projection_ref": target_projection_ref,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_code_section_projection", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionProjectionEdge):
            return value
        return CodeSectionProjectionEdge.validate_invocation_value(value)


class CodeSectionProjectionEdgeBuildViaCodeSectionProjectionInput(BaseModel):
    code_section_projection_id: UUID = Field(description="Foreign key for CodeSectionProjection.projection_edges")
    member: str
    type_ref: str
    target_projection_ref: str | None = Field(default=None)


class CodeSectionProjectionEdgeBuildViaCodeSectionProjectionOutput(BaseModel):
    value: CodeSectionProjectionEdge


FUNCTIONS = {
    "CodeSectionProjectionEdge": {
        "build_via_code_section_projection": {
            "canonical": {
                "name": "build_via_code_section_projection",
                "description": "Build a deterministic projection-edge entry under a projection.",
                "is_constructor": True,
            },
            "input": CodeSectionProjectionEdgeBuildViaCodeSectionProjectionInput,
            "output": CodeSectionProjectionEdgeBuildViaCodeSectionProjectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionProjectionEdge",
    "CodeSectionProjectionEdgeBuildViaCodeSectionProjectionInput",
    "CodeSectionProjectionEdgeBuildViaCodeSectionProjectionOutput",
    "FUNCTIONS",
]
