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
    from aware_attention_ontology.layout.layout import Layout
    from aware_interface_ontology.window.window_layout_section import WindowLayoutSection


class WindowLayout(ORMModel):
    """Window attachment/state for a canonical shareable Layout."""

    # Relationships
    layout: Layout | None = Field(default=None, exclude=True)
    layout_sections: list[WindowLayoutSection] = Field(default_factory=list, exclude=True)

    # Foreign Keys
    window_id: UUID = Field(description="Foreign key for Window.layouts")
    layout_id: UUID = Field(description="Foreign key for WindowLayout.layout")

    async def add_layout_section(
        self, layout_section_id: UUID, projection_experience_view_id: UUID
    ) -> WindowLayoutSection:
        """Attach one section binding under this WindowLayout."""

        payload = {
            "layout_section_id": layout_section_id,
            "projection_experience_view_id": projection_experience_view_id,
        }
        result = await invoke_instance(orm_model=self, function_name="add_layout_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.window.window_layout_section import WindowLayoutSection

        if isinstance(value, WindowLayoutSection):
            return value
        return WindowLayoutSection.validate_invocation_value(value)

    @classmethod
    async def build_via_window(cls, window_id: UUID, layout_id: UUID) -> WindowLayout:
        """Builds a deterministic WindowLayout attachment for (window, layout)."""

        payload = {"window_id": window_id, "layout_id": layout_id}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_window", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, WindowLayout):
            return value
        return WindowLayout.validate_invocation_value(value)


class WindowLayoutAddLayoutSectionInput(BaseModel):
    layout_section_id: UUID
    projection_experience_view_id: UUID


class WindowLayoutAddLayoutSectionOutput(BaseModel):
    value: WindowLayoutSection


class WindowLayoutBuildViaWindowInput(BaseModel):
    window_id: UUID = Field(description="Foreign key for Window.layouts")
    layout_id: UUID


class WindowLayoutBuildViaWindowOutput(BaseModel):
    value: WindowLayout


FUNCTIONS = {
    "WindowLayout": {
        "add_layout_section": {
            "canonical": {
                "name": "add_layout_section",
                "description": "Attach one section binding under this WindowLayout.",
                "is_constructor": False,
            },
            "input": WindowLayoutAddLayoutSectionInput,
            "output": WindowLayoutAddLayoutSectionOutput,
        },
        "build_via_window": {
            "canonical": {
                "name": "build_via_window",
                "description": "Builds a deterministic WindowLayout attachment for (window, layout).",
                "is_constructor": True,
            },
            "input": WindowLayoutBuildViaWindowInput,
            "output": WindowLayoutBuildViaWindowOutput,
        },
    },
}

__all__ = [
    "WindowLayout",
    "WindowLayoutAddLayoutSectionInput",
    "WindowLayoutAddLayoutSectionOutput",
    "WindowLayoutBuildViaWindowInput",
    "WindowLayoutBuildViaWindowOutput",
    "FUNCTIONS",
]
