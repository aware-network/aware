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
    from aware_attention_ontology.layout.layout_config import LayoutConfig
    from aware_experience_ontology.projection.projection_experience_layout_section_graph_binding import (
        ProjectionExperienceLayoutSectionGraphBinding,
    )


class ProjectionExperienceLayoutGraphBinding(ORMModel):
    """
    ProjectionExperience-owned layout graph binding contract.
    Contract:
    - Declares one stable coordination agreement between an Attention layout and
    a set of Experience-owned section graph bindings.
    - Keeps apps and Interface packages from selecting section bindings or pane
    defaults directly.
    - Does not own ordering or runtime activation; Attention layout topology and
    sessions own those resolutions.
    """

    # Relationships
    layout_config: LayoutConfig | None = Field(default=None, exclude=True)
    layout_section_graph_bindings: list[ProjectionExperienceLayoutSectionGraphBinding] = Field(
        default_factory=list, exclude=True
    )

    # Attributes
    binding_key: str

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_layout_graph_bindings"
    )
    layout_config_id: UUID = Field(description="Foreign key for ProjectionExperienceLayoutGraphBinding.layout_config")

    async def add_section_graph_binding(
        self, section_graph_binding_id: UUID
    ) -> ProjectionExperienceLayoutSectionGraphBinding:
        """
        Attach one existing section graph binding to this layout composition.

        Contract:
        - The section binding remains the source of view + section + graph anchor truth.
        - This row only groups section bindings under one layout-level Experience target.
        - Ordering is resolved from the Attention LayoutConfigSectionConfig relation.
        """

        payload = {"section_graph_binding_id": section_graph_binding_id}
        result = await invoke_instance(orm_model=self, function_name="add_section_graph_binding", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_layout_section_graph_binding import (
            ProjectionExperienceLayoutSectionGraphBinding,
        )

        if isinstance(value, ProjectionExperienceLayoutSectionGraphBinding):
            return value
        return ProjectionExperienceLayoutSectionGraphBinding.validate_invocation_value(value)

    @classmethod
    async def build_via_projection_experience(
        cls, projection_experience_id: UUID, layout_config_id: UUID, binding_key: str
    ) -> ProjectionExperienceLayoutGraphBinding:
        """
        Create deterministic ProjectionExperienceLayoutGraphBinding under one ProjectionExperience.

        Contract:
        - `binding_key` is the stable service-facing layout composition handle.
        - `layout_config` is the canonical portal to Attention-owned layout truth.
        - Child section rows must target sections that belong to this layout.
        """

        payload = {
            "projection_experience_id": projection_experience_id,
            "layout_config_id": layout_config_id,
            "binding_key": binding_key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceLayoutGraphBinding):
            return value
        return ProjectionExperienceLayoutGraphBinding.validate_invocation_value(value)


class ProjectionExperienceLayoutGraphBindingAddSectionGraphBindingInput(BaseModel):
    section_graph_binding_id: UUID


class ProjectionExperienceLayoutGraphBindingAddSectionGraphBindingOutput(BaseModel):
    value: ProjectionExperienceLayoutSectionGraphBinding


class ProjectionExperienceLayoutGraphBindingBuildViaProjectionExperienceInput(BaseModel):
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_layout_graph_bindings"
    )
    layout_config_id: UUID
    binding_key: str


class ProjectionExperienceLayoutGraphBindingBuildViaProjectionExperienceOutput(BaseModel):
    value: ProjectionExperienceLayoutGraphBinding


FUNCTIONS = {
    "ProjectionExperienceLayoutGraphBinding": {
        "add_section_graph_binding": {
            "canonical": {
                "name": "add_section_graph_binding",
                "description": "Attach one existing section graph binding to this layout composition.\n\nContract:\n- The section binding remains the source of view + section + graph anchor truth.\n- This row only groups section bindings under one layout-level Experience target.\n- Ordering is resolved from the Attention LayoutConfigSectionConfig relation.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceLayoutGraphBindingAddSectionGraphBindingInput,
            "output": ProjectionExperienceLayoutGraphBindingAddSectionGraphBindingOutput,
        },
        "build_via_projection_experience": {
            "canonical": {
                "name": "build_via_projection_experience",
                "description": "Create deterministic ProjectionExperienceLayoutGraphBinding under one ProjectionExperience.\n\nContract:\n- `binding_key` is the stable service-facing layout composition handle.\n- `layout_config` is the canonical portal to Attention-owned layout truth.\n- Child section rows must target sections that belong to this layout.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceLayoutGraphBindingBuildViaProjectionExperienceInput,
            "output": ProjectionExperienceLayoutGraphBindingBuildViaProjectionExperienceOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceLayoutGraphBinding",
    "ProjectionExperienceLayoutGraphBindingAddSectionGraphBindingInput",
    "ProjectionExperienceLayoutGraphBindingAddSectionGraphBindingOutput",
    "ProjectionExperienceLayoutGraphBindingBuildViaProjectionExperienceInput",
    "ProjectionExperienceLayoutGraphBindingBuildViaProjectionExperienceOutput",
    "FUNCTIONS",
]
