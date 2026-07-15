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


class CodeSectionBindingMap(ORMModel):
    # Relationships
    name_segment: ContentPartTextSegment
    source_segment: ContentPartTextSegment
    target_segment: ContentPartTextSegment
    body_segment: ContentPartTextSegment | None = Field(default=None)
    template_segment: ContentPartTextSegment | None = Field(default=None)

    # Attributes
    name: str
    source_ref: str
    target_ref: str
    description: str | None = Field(default=None)
    template_text: str | None = Field(default=None)

    # Foreign Keys
    code_section_binding_id: UUID = Field(description="Foreign key for CodeSectionBinding.code_section_binding_maps")
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionBindingMap.name_segment")
    source_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionBindingMap.source_segment"
    )
    target_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionBindingMap.target_segment"
    )
    body_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionBindingMap.body_segment")
    template_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionBindingMap.template_segment"
    )

    @classmethod
    async def build_via_code_section_binding(
        cls,
        code_section_binding_id: UUID,
        name: str,
        source_ref: str,
        target_ref: str,
        description: str | None = None,
        template_text: str | None = None,
    ) -> CodeSectionBindingMap:
        """Build a deterministic binding-map entry under a binding."""

        payload = {
            "code_section_binding_id": code_section_binding_id,
            "name": name,
            "source_ref": source_ref,
            "target_ref": target_ref,
            "description": description,
            "template_text": template_text,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_code_section_binding", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionBindingMap):
            return value
        return CodeSectionBindingMap.validate_invocation_value(value)


class CodeSectionBindingMapBuildViaCodeSectionBindingInput(BaseModel):
    code_section_binding_id: UUID = Field(description="Foreign key for CodeSectionBinding.code_section_binding_maps")
    name: str
    source_ref: str
    target_ref: str
    description: str | None = Field(default=None)
    template_text: str | None = Field(default=None)


class CodeSectionBindingMapBuildViaCodeSectionBindingOutput(BaseModel):
    value: CodeSectionBindingMap


FUNCTIONS = {
    "CodeSectionBindingMap": {
        "build_via_code_section_binding": {
            "canonical": {
                "name": "build_via_code_section_binding",
                "description": "Build a deterministic binding-map entry under a binding.",
                "is_constructor": True,
            },
            "input": CodeSectionBindingMapBuildViaCodeSectionBindingInput,
            "output": CodeSectionBindingMapBuildViaCodeSectionBindingOutput,
        },
    },
}

__all__ = [
    "CodeSectionBindingMap",
    "CodeSectionBindingMapBuildViaCodeSectionBindingInput",
    "CodeSectionBindingMapBuildViaCodeSectionBindingOutput",
    "FUNCTIONS",
]
