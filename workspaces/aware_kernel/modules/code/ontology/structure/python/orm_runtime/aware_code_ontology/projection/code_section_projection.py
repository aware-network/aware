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
    from aware_code_ontology.code.code_section import CodeSection
    from aware_code_ontology.comment.code_section_comment import CodeSectionComment
    from aware_code_ontology.projection.code_section_projection_edge import CodeSectionProjectionEdge
    from aware_code_ontology.projection.code_section_projection_view import CodeSectionProjectionView
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment


class CodeSectionProjection(ORMModel):
    # Relationships
    code_section_comments: list[CodeSectionComment] = Field(default_factory=list)
    name_segment: ContentPartTextSegment
    root_type_segment: ContentPartTextSegment | None = Field(default=None)
    projection_edges: list[CodeSectionProjectionEdge] = Field(default_factory=list)
    projection_views: list[CodeSectionProjectionView] = Field(default_factory=list)
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_projection")

    # Attributes
    name: str = Field(description="Projection symbol name (e.g. `ActorFocus`).")
    description: str | None = Field(default=None, description="Human-friendly description (derived from doc comments).")
    projection_name: str = Field(
        description='Canonical projection identity name (default: authored projection symbol; overridable via `name "..."` option).'
    )
    label: str | None = Field(default=None)
    is_branchable: bool = Field(default=False)
    root_type_ref: str | None = Field(default=None, description="Root type reference (FQN) for the projection.")

    # Foreign Keys
    code_section_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSection.code_section_projection"
    )
    name_segment_id: UUID | None = Field(default=None, description="Foreign key for CodeSectionProjection.name_segment")
    root_type_segment_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSectionProjection.root_type_segment"
    )

    async def create_edge(
        self, member: str, type_ref: str, target_projection_ref: str | None = None
    ) -> CodeSectionProjectionEdge:
        """Create a deterministic projection-edge entry under this projection."""

        payload = {"member": member, "type_ref": type_ref, "target_projection_ref": target_projection_ref}
        result = await invoke_instance(orm_model=self, function_name="create_edge", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.projection.code_section_projection_edge import CodeSectionProjectionEdge

        if isinstance(value, CodeSectionProjectionEdge):
            return value
        return CodeSectionProjectionEdge.validate_invocation_value(value)

    async def create_view(
        self, key: str, kind: str, is_default: bool = False, description: str | None = None
    ) -> CodeSectionProjectionView:
        """Create a deterministic projection-view entry under this projection."""

        payload = {"key": key, "kind": kind, "is_default": is_default, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_view", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.projection.code_section_projection_view import CodeSectionProjectionView

        if isinstance(value, CodeSectionProjectionView):
            return value
        return CodeSectionProjectionView.validate_invocation_value(value)

    @classmethod
    async def build_via_code_section(cls, code_section_id: UUID) -> CodeSectionProjection:
        """Build the projection payload under a CodeSection."""

        payload = {"code_section_id": code_section_id}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSectionProjection):
            return value
        return CodeSectionProjection.validate_invocation_value(value)


class CodeSectionProjectionCreateEdgeInput(BaseModel):
    member: str
    type_ref: str
    target_projection_ref: str | None = Field(default=None)


class CodeSectionProjectionCreateEdgeOutput(BaseModel):
    value: CodeSectionProjectionEdge


class CodeSectionProjectionCreateViewInput(BaseModel):
    key: str
    kind: str
    is_default: bool = Field(default=False)
    description: str | None = Field(default=None)


class CodeSectionProjectionCreateViewOutput(BaseModel):
    value: CodeSectionProjectionView


class CodeSectionProjectionBuildViaCodeSectionInput(BaseModel):
    code_section_id: UUID = Field(description="Foreign key for CodeSection.code_section_projection")


class CodeSectionProjectionBuildViaCodeSectionOutput(BaseModel):
    value: CodeSectionProjection


FUNCTIONS = {
    "CodeSectionProjection": {
        "create_edge": {
            "canonical": {
                "name": "create_edge",
                "description": "Create a deterministic projection-edge entry under this projection.",
                "is_constructor": False,
            },
            "input": CodeSectionProjectionCreateEdgeInput,
            "output": CodeSectionProjectionCreateEdgeOutput,
        },
        "create_view": {
            "canonical": {
                "name": "create_view",
                "description": "Create a deterministic projection-view entry under this projection.",
                "is_constructor": False,
            },
            "input": CodeSectionProjectionCreateViewInput,
            "output": CodeSectionProjectionCreateViewOutput,
        },
        "build_via_code_section": {
            "canonical": {
                "name": "build_via_code_section",
                "description": "Build the projection payload under a CodeSection.",
                "is_constructor": True,
            },
            "input": CodeSectionProjectionBuildViaCodeSectionInput,
            "output": CodeSectionProjectionBuildViaCodeSectionOutput,
        },
    },
}

__all__ = [
    "CodeSectionProjection",
    "CodeSectionProjectionCreateEdgeInput",
    "CodeSectionProjectionCreateEdgeOutput",
    "CodeSectionProjectionCreateViewInput",
    "CodeSectionProjectionCreateViewOutput",
    "CodeSectionProjectionBuildViaCodeSectionInput",
    "CodeSectionProjectionBuildViaCodeSectionOutput",
    "FUNCTIONS",
]
