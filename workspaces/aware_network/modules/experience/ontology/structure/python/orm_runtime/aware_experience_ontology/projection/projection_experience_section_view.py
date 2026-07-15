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
    from aware_experience_ontology.projection.projection_experience_view_instance import (
        ProjectionExperienceViewInstance,
    )


class ProjectionExperienceSectionView(ORMModel):
    """
    Section-scoped resolver from a concrete view instance to one Attention section.
    Contract:
    - Attention may select Observable through Section -> FocusScope.
    - Experience resolves Section + selected Observable by deriving Observable
    from the linked view instance's ProjectionExperienceView.api_view.
    - One Observable may have many view configurations globally, but this bridge
    selects the concrete view instance for one ProjectionExperienceSection.
    """

    # Relationships
    projection_experience_view_instance: ProjectionExperienceViewInstance | None = Field(default=None)

    # Attributes
    status: str = Field(default="active")

    # Foreign Keys
    projection_experience_section_id: UUID = Field(
        description="Foreign key for ProjectionExperienceSection.section_views"
    )
    projection_experience_view_instance_id: UUID = Field(
        description="Foreign key for ProjectionExperienceSectionView.projection_experience_view_instance"
    )

    @classmethod
    async def build_via_projection_experience_section(
        cls,
        projection_experience_section_id: UUID,
        projection_experience_view_instance_id: UUID,
        status: str = "active",
    ) -> ProjectionExperienceSectionView:
        """
        Create one section+view-instance resolver.

        Contract:
        - Identity is scoped by parent ProjectionExperienceSection plus view instance.
        - `projection_experience_view_instance` must be the concrete view fulfillment
          for the ApiView whose observable may be selected by Attention.
        """

        payload = {
            "projection_experience_section_id": projection_experience_section_id,
            "projection_experience_view_instance_id": projection_experience_view_instance_id,
            "status": status,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_section", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceSectionView):
            return value
        return ProjectionExperienceSectionView.validate_invocation_value(value)


class ProjectionExperienceSectionViewBuildViaProjectionExperienceSectionInput(BaseModel):
    projection_experience_section_id: UUID = Field(
        description="Foreign key for ProjectionExperienceSection.section_views"
    )
    projection_experience_view_instance_id: UUID
    status: str = Field(default="active")


class ProjectionExperienceSectionViewBuildViaProjectionExperienceSectionOutput(BaseModel):
    value: ProjectionExperienceSectionView


FUNCTIONS = {
    "ProjectionExperienceSectionView": {
        "build_via_projection_experience_section": {
            "canonical": {
                "name": "build_via_projection_experience_section",
                "description": "Create one section+view-instance resolver.\n\nContract:\n- Identity is scoped by parent ProjectionExperienceSection plus view instance.\n- `projection_experience_view_instance` must be the concrete view fulfillment\n  for the ApiView whose observable may be selected by Attention.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceSectionViewBuildViaProjectionExperienceSectionInput,
            "output": ProjectionExperienceSectionViewBuildViaProjectionExperienceSectionOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceSectionView",
    "ProjectionExperienceSectionViewBuildViaProjectionExperienceSectionInput",
    "ProjectionExperienceSectionViewBuildViaProjectionExperienceSectionOutput",
    "FUNCTIONS",
]
