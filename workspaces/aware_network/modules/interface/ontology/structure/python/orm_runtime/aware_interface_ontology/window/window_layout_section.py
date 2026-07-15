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
    from aware_attention_ontology.layout.layout_section import LayoutSection
    from aware_experience_ontology.projection.projection_experience_view import ProjectionExperienceView


class WindowLayoutSection(ORMModel):
    """Attention Section (observable representation unit) to Experience View (rendering target)"""

    # Relationships
    layout_section: LayoutSection | None = Field(default=None, exclude=True)
    projection_experience_view: ProjectionExperienceView | None = Field(default=None, exclude=True)

    # Foreign Keys
    window_layout_id: UUID = Field(description="Foreign key for WindowLayout.layout_sections")
    layout_section_id: UUID = Field(description="Foreign key for WindowLayoutSection.layout_section")
    projection_experience_view_id: UUID = Field(
        description="Foreign key for WindowLayoutSection.projection_experience_view"
    )

    @classmethod
    async def build_via_window_layout(
        cls, window_layout_id: UUID, layout_section_id: UUID, projection_experience_view_id: UUID
    ) -> WindowLayoutSection:
        """Builds a deterministic WindowLayoutSection attachment for (window_layout, layout_section)."""

        payload = {
            "window_layout_id": window_layout_id,
            "layout_section_id": layout_section_id,
            "projection_experience_view_id": projection_experience_view_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_window_layout", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, WindowLayoutSection):
            return value
        return WindowLayoutSection.validate_invocation_value(value)


class WindowLayoutSectionBuildViaWindowLayoutInput(BaseModel):
    window_layout_id: UUID = Field(description="Foreign key for WindowLayout.layout_sections")
    layout_section_id: UUID
    projection_experience_view_id: UUID


class WindowLayoutSectionBuildViaWindowLayoutOutput(BaseModel):
    value: WindowLayoutSection


FUNCTIONS = {
    "WindowLayoutSection": {
        "build_via_window_layout": {
            "canonical": {
                "name": "build_via_window_layout",
                "description": "Builds a deterministic WindowLayoutSection attachment for (window_layout, layout_section).",
                "is_constructor": True,
            },
            "input": WindowLayoutSectionBuildViaWindowLayoutInput,
            "output": WindowLayoutSectionBuildViaWindowLayoutOutput,
        },
    },
}

__all__ = [
    "WindowLayoutSection",
    "WindowLayoutSectionBuildViaWindowLayoutInput",
    "WindowLayoutSectionBuildViaWindowLayoutOutput",
    "FUNCTIONS",
]
