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
    from aware_code_ontology.binding.code_section_binding_map import CodeSectionBindingMap
    from aware_code_ontology.code.code_section import CodeSection
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionBinding(ORMModel):
    # Relationships
    source_graph_segment: ContentPartTextSegment
    target_graph_segment: ContentPartTextSegment
    code_section_binding_maps: list[CodeSectionBindingMap] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_binding")

    # Attributes
    source_graph_ref: str
    target_graph_ref: str

    # Foreign Keys
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeSection.code_section_binding")
    source_graph_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionBinding.source_graph_segment"
    )
    target_graph_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionBinding.target_graph_segment"
    )

    async def create_map(
        self,
        name: str,
        source_ref: str,
        target_ref: str,
        description: str | None = None,
        template_text: str | None = None,
    ) -> CodeSectionBindingMap:
        """Create a deterministic binding-map entry under this binding."""

        payload = {
            "name": name,
            "source_ref": source_ref,
            "target_ref": target_ref,
            "description": description,
            "template_text": template_text,
        }
        result = await invoke_instance(orm_model=self, function_name="create_map", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.binding.code_section_binding_map import CodeSectionBindingMap

        if isinstance(value, CodeSectionBindingMap):
            return value
        return CodeSectionBindingMap.validate_invocation_value(value)

    @classmethod
    async def build_via_code_section(cls, code_section_id: UUID) -> CodeSectionBinding:
        """Build the binding payload under a CodeSection."""

        payload = {"code_section_id": code_section_id}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionBinding):
            return value
        return CodeSectionBinding.validate_invocation_value(value)


class CodeSectionBindingCreateMapInput(BaseModel):
    name: str
    source_ref: str
    target_ref: str
    description: str | None = Field(default=None)
    template_text: str | None = Field(default=None)


class CodeSectionBindingCreateMapOutput(BaseModel):
    value: CodeSectionBindingMap


class CodeSectionBindingBuildViaCodeSectionInput(BaseModel):
    code_section_id: UUID = Field(description="Foreign key for CodeSection.code_section_binding")


class CodeSectionBindingBuildViaCodeSectionOutput(BaseModel):
    value: CodeSectionBinding


FUNCTIONS = {
    "CodeSectionBinding": {
        "create_map": {
            "canonical": {
                "name": "create_map",
                "description": "Create a deterministic binding-map entry under this binding.",
                "is_constructor": False,
            },
            "input": CodeSectionBindingCreateMapInput,
            "output": CodeSectionBindingCreateMapOutput,
        },
        "build_via_code_section": {
            "canonical": {
                "name": "build_via_code_section",
                "description": "Build the binding payload under a CodeSection.",
                "is_constructor": True,
            },
            "input": CodeSectionBindingBuildViaCodeSectionInput,
            "output": CodeSectionBindingBuildViaCodeSectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionBinding",
    "CodeSectionBindingCreateMapInput",
    "CodeSectionBindingCreateMapOutput",
    "CodeSectionBindingBuildViaCodeSectionInput",
    "CodeSectionBindingBuildViaCodeSectionOutput",
    "FUNCTIONS",
]
