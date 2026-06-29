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


class CodeSectionProjectionView(ORMModel):
    # Relationships
    key_segment: ContentPartTextSegment
    body_segment: ContentPartTextSegment

    # Attributes
    key: str = Field(description="Fully qualified view key within the projection (e.g. `onboarding.welcome`).")
    kind: str = Field(description="One of: `construct`, `instance`.")
    is_default: bool = Field(default=False)
    description: str | None = Field(default=None)

    # Foreign Keys
    code_section_projection_id: UUID = Field(description="Foreign key for CodeSectionProjection.projection_views")
    key_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionProjectionView.key_segment"
    )
    body_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionProjectionView.body_segment"
    )

    @classmethod
    async def build_via_code_section_projection(
        cls,
        code_section_projection_id: UUID,
        key: str,
        kind: str,
        is_default: bool = False,
        description: str | None = None,
    ) -> CodeSectionProjectionView:
        """Build a deterministic projection-view entry under a projection."""

        payload = {
            "code_section_projection_id": code_section_projection_id,
            "key": key,
            "kind": kind,
            "is_default": is_default,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_code_section_projection", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionProjectionView):
            return value
        return CodeSectionProjectionView.validate_invocation_value(value)


class CodeSectionProjectionViewBuildViaCodeSectionProjectionInput(BaseModel):
    code_section_projection_id: UUID = Field(description="Foreign key for CodeSectionProjection.projection_views")
    key: str
    kind: str
    is_default: bool = Field(default=False)
    description: str | None = Field(default=None)


class CodeSectionProjectionViewBuildViaCodeSectionProjectionOutput(BaseModel):
    value: CodeSectionProjectionView


FUNCTIONS = {
    "CodeSectionProjectionView": {
        "build_via_code_section_projection": {
            "canonical": {
                "name": "build_via_code_section_projection",
                "description": "Build a deterministic projection-view entry under a projection.",
                "is_constructor": True,
            },
            "input": CodeSectionProjectionViewBuildViaCodeSectionProjectionInput,
            "output": CodeSectionProjectionViewBuildViaCodeSectionProjectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionProjectionView",
    "CodeSectionProjectionViewBuildViaCodeSectionProjectionInput",
    "CodeSectionProjectionViewBuildViaCodeSectionProjectionOutput",
    "FUNCTIONS",
]
