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
    from aware_attention_ontology.layout.layout_config_section_config import LayoutConfigSectionConfig
    from aware_experience_ontology.projection.projection_experience_graph_identity import (
        ProjectionExperienceGraphIdentity,
    )
    from aware_experience_ontology.projection.projection_experience_view import ProjectionExperienceView


class ProjectionExperienceSectionGraphBinding(ORMModel):
    """
    ProjectionExperience-owned section graph binding contract.
    Contract:
    - Declares one stable coordination agreement between an Attention layout section,
    one Experience view, and one ProjectionExperienceGraphIdentity.
    - Keeps the graph-occurrence anchor explicit without coupling Interface pane
    mounts to one focused runtime object.
    """

    # Relationships
    layout_config_section_config: LayoutConfigSectionConfig | None = Field(default=None, exclude=True)
    projection_experience_view: ProjectionExperienceView | None = Field(default=None, exclude=True)
    projection_experience_graph_identity: ProjectionExperienceGraphIdentity | None = Field(default=None, exclude=True)

    # Attributes
    binding_key: str
    section_key: str = Field(
        description="Denormalized lookup key derived from the target Attention layout section.\nAuthoritative section topology is `layout_config_section_config`."
    )

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_section_graph_bindings"
    )
    layout_config_section_config_id: UUID = Field(
        description="Foreign key for ProjectionExperienceSectionGraphBinding.layout_config_section_config"
    )
    projection_experience_view_id: UUID = Field(
        description="Foreign key for ProjectionExperienceSectionGraphBinding.projection_experience_view"
    )
    projection_experience_graph_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceSectionGraphBinding.projection_experience_graph_identity"
    )

    @classmethod
    async def build_via_projection_experience(
        cls,
        projection_experience_id: UUID,
        layout_config_section_config_id: UUID,
        projection_experience_view_id: UUID,
        projection_experience_graph_identity_id: UUID,
        binding_key: str,
        section_key: str,
    ) -> ProjectionExperienceSectionGraphBinding:
        """
        Create deterministic ProjectionExperienceSectionGraphBinding under one ProjectionExperience.

        Contract:
        - `binding_key` is the stable service-facing coordination handle.
        - `layout_config_section_config` is the canonical portal to Attention-owned layout section truth.
        - `section_key` is a denormalized lookup/cache key for service filters and must match the target
        layout section.
        - `projection_experience_graph_identity` is the explicit occurrence anchor for lawful coordination.
        """

        payload = {
            "projection_experience_id": projection_experience_id,
            "layout_config_section_config_id": layout_config_section_config_id,
            "projection_experience_view_id": projection_experience_view_id,
            "projection_experience_graph_identity_id": projection_experience_graph_identity_id,
            "binding_key": binding_key,
            "section_key": section_key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceSectionGraphBinding):
            return value
        return ProjectionExperienceSectionGraphBinding.validate_invocation_value(value)


class ProjectionExperienceSectionGraphBindingBuildViaProjectionExperienceInput(BaseModel):
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_section_graph_bindings"
    )
    layout_config_section_config_id: UUID
    projection_experience_view_id: UUID
    projection_experience_graph_identity_id: UUID
    binding_key: str
    section_key: str


class ProjectionExperienceSectionGraphBindingBuildViaProjectionExperienceOutput(BaseModel):
    value: ProjectionExperienceSectionGraphBinding


FUNCTIONS = {
    "ProjectionExperienceSectionGraphBinding": {
        "build_via_projection_experience": {
            "canonical": {
                "name": "build_via_projection_experience",
                "description": "Create deterministic ProjectionExperienceSectionGraphBinding under one ProjectionExperience.\n\nContract:\n- `binding_key` is the stable service-facing coordination handle.\n- `layout_config_section_config` is the canonical portal to Attention-owned layout section truth.\n- `section_key` is a denormalized lookup/cache key for service filters and must match the target layout section.\n- `projection_experience_graph_identity` is the explicit occurrence anchor for lawful coordination.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceSectionGraphBindingBuildViaProjectionExperienceInput,
            "output": ProjectionExperienceSectionGraphBindingBuildViaProjectionExperienceOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceSectionGraphBinding",
    "ProjectionExperienceSectionGraphBindingBuildViaProjectionExperienceInput",
    "ProjectionExperienceSectionGraphBindingBuildViaProjectionExperienceOutput",
    "FUNCTIONS",
]
