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
    from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
        ProjectionExperienceSectionGraphBinding,
    )


class ProjectionExperienceLayoutSectionGraphBinding(ORMModel):
    """
    Section graph binding row under ProjectionExperienceLayoutGraphBinding.
    Contract:
    - Groups one existing ProjectionExperienceSectionGraphBinding under one
    layout graph binding.
    - Does not duplicate section, view, graph, or order fields.
    - The parent layout binding validates that the section binding targets a
    section inside the parent Attention LayoutConfig.
    """

    # Relationships
    section_graph_binding: ProjectionExperienceSectionGraphBinding | None = Field(default=None, exclude=True)

    # Foreign Keys
    projection_experience_layout_graph_binding_id: UUID = Field(
        description="Foreign key for ProjectionExperienceLayoutGraphBinding.layout_section_graph_bindings"
    )
    section_graph_binding_id: UUID = Field(
        description="Foreign key for ProjectionExperienceLayoutSectionGraphBinding.section_graph_binding"
    )

    @classmethod
    async def build_via_projection_experience_layout_graph_binding(
        cls, projection_experience_layout_graph_binding_id: UUID, section_graph_binding_id: UUID
    ) -> ProjectionExperienceLayoutSectionGraphBinding:
        """Create deterministic ProjectionExperienceLayoutSectionGraphBinding."""

        payload = {
            "projection_experience_layout_graph_binding_id": projection_experience_layout_graph_binding_id,
            "section_graph_binding_id": section_graph_binding_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_layout_graph_binding", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceLayoutSectionGraphBinding):
            return value
        return ProjectionExperienceLayoutSectionGraphBinding.validate_invocation_value(value)


class ProjectionExperienceLayoutSectionGraphBindingBuildViaProjectionExperienceLayoutGraphBindingInput(BaseModel):
    projection_experience_layout_graph_binding_id: UUID = Field(
        description="Foreign key for ProjectionExperienceLayoutGraphBinding.layout_section_graph_bindings"
    )
    section_graph_binding_id: UUID


class ProjectionExperienceLayoutSectionGraphBindingBuildViaProjectionExperienceLayoutGraphBindingOutput(BaseModel):
    value: ProjectionExperienceLayoutSectionGraphBinding


FUNCTIONS = {
    "ProjectionExperienceLayoutSectionGraphBinding": {
        "build_via_projection_experience_layout_graph_binding": {
            "canonical": {
                "name": "build_via_projection_experience_layout_graph_binding",
                "description": "Create deterministic ProjectionExperienceLayoutSectionGraphBinding.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceLayoutSectionGraphBindingBuildViaProjectionExperienceLayoutGraphBindingInput,
            "output": ProjectionExperienceLayoutSectionGraphBindingBuildViaProjectionExperienceLayoutGraphBindingOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceLayoutSectionGraphBinding",
    "ProjectionExperienceLayoutSectionGraphBindingBuildViaProjectionExperienceLayoutGraphBindingInput",
    "ProjectionExperienceLayoutSectionGraphBindingBuildViaProjectionExperienceLayoutGraphBindingOutput",
    "FUNCTIONS",
]
