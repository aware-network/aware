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
    from aware_attention_ontology.section.section import Section
    from aware_experience_ontology.projection.projection_experience_section_view import ProjectionExperienceSectionView


class ProjectionExperienceSection(ORMModel):
    """
    Experience-owned bridge from ProjectionExperience to an Attention Section.
    Contract:
    - Attention owns Section and FocusScope mutation.
    - Experience owns how one Section resolves to a concrete view instance for
    this ProjectionExperience.
    - Selected Observable matching is derived through the linked view's ApiView.
    - This object does not represent an Environment, Interface, window, layout
    runtime, or focus-scope mount.
    """

    # Relationships
    section: Section | None = Field(default=None)
    section_views: list[ProjectionExperienceSectionView] = Field(default_factory=list)

    # Attributes
    section_key: str | None = Field(
        default=None, description="Optional denormalized lookup text from the Attention Section."
    )

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_sections"
    )
    section_id: UUID = Field(description="Foreign key for ProjectionExperienceSection.section")

    async def bind_view(
        self, projection_experience_view_instance_id: UUID, status: str = "active"
    ) -> ProjectionExperienceSectionView:
        """
        Bind one concrete view instance to this section.

        Contract:
        - Identity is section + view instance.
        - The linked view instance carries view/config/branch/action provenance.
        - Observable matching is derived from the linked view's ApiView contract.
        - FocusScope remains mutable Attention selection state and is not part of
          this bridge's identity.
        """

        payload = {"projection_experience_view_instance_id": projection_experience_view_instance_id, "status": status}
        result = await invoke_instance(orm_model=self, function_name="bind_view", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_section_view import (
            ProjectionExperienceSectionView,
        )

        if isinstance(value, ProjectionExperienceSectionView):
            return value
        return ProjectionExperienceSectionView.validate_invocation_value(value)

    @classmethod
    async def build_via_projection_experience(
        cls, projection_experience_id: UUID, section_id: UUID, section_key: str | None = None
    ) -> ProjectionExperienceSection:
        """
        Create one ProjectionExperience-scoped Attention Section bridge.

        Contract:
        - The relationship to Attention Section is the only Attention-owned coordinate here.
        - Section-key text is denormalized for lookup/debugging only.
        """

        payload = {
            "projection_experience_id": projection_experience_id,
            "section_id": section_id,
            "section_key": section_key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceSection):
            return value
        return ProjectionExperienceSection.validate_invocation_value(value)


class ProjectionExperienceSectionBindViewInput(BaseModel):
    projection_experience_view_instance_id: UUID
    status: str = Field(default="active")


class ProjectionExperienceSectionBindViewOutput(BaseModel):
    value: ProjectionExperienceSectionView


class ProjectionExperienceSectionBuildViaProjectionExperienceInput(BaseModel):
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_sections"
    )
    section_id: UUID
    section_key: str | None = Field(default=None)


class ProjectionExperienceSectionBuildViaProjectionExperienceOutput(BaseModel):
    value: ProjectionExperienceSection


FUNCTIONS = {
    "ProjectionExperienceSection": {
        "bind_view": {
            "canonical": {
                "name": "bind_view",
                "description": "Bind one concrete view instance to this section.\n\nContract:\n- Identity is section + view instance.\n- The linked view instance carries view/config/branch/action provenance.\n- Observable matching is derived from the linked view's ApiView contract.\n- FocusScope remains mutable Attention selection state and is not part of\n  this bridge's identity.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceSectionBindViewInput,
            "output": ProjectionExperienceSectionBindViewOutput,
        },
        "build_via_projection_experience": {
            "canonical": {
                "name": "build_via_projection_experience",
                "description": "Create one ProjectionExperience-scoped Attention Section bridge.\n\nContract:\n- The relationship to Attention Section is the only Attention-owned coordinate here.\n- Section-key text is denormalized for lookup/debugging only.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceSectionBuildViaProjectionExperienceInput,
            "output": ProjectionExperienceSectionBuildViaProjectionExperienceOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceSection",
    "ProjectionExperienceSectionBindViewInput",
    "ProjectionExperienceSectionBindViewOutput",
    "ProjectionExperienceSectionBuildViaProjectionExperienceInput",
    "ProjectionExperienceSectionBuildViaProjectionExperienceOutput",
    "FUNCTIONS",
]
