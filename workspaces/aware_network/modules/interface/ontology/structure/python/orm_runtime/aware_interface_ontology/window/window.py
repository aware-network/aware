from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology
from aware_interface_ontology.window.window_enums import WindowActiveLayoutMode

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_attention_ontology.layout.layout import Layout
    from aware_interface_ontology.window.window_layout import WindowLayout


class Window(ORMModel):
    """
    Window exposes Interface-owned visible layout state.
    Contract:
    - Environment/Thread owns shared active layout truth.
    - InterfaceWindow owns the protected thread target.
    - Window.active_layout is a direct visible Attention Layout pointer for replayable renderer state.
    - WindowLayout remains compatibility/override/cached section-binding state, not the normal selector.
    """

    # Relationships
    layouts: list[WindowLayout] = Field(default_factory=list, exclude=True)
    active_layout: Layout | None = Field(default=None, exclude=True)

    # Attributes
    window_id: UUID
    active_layout_mode: WindowActiveLayoutMode = Field(default=WindowActiveLayoutMode.follow_thread_active)

    # Foreign Keys
    active_layout_id: UUID | None = Field(default=None, description="Foreign key for Window.active_layout")

    @classmethod
    async def build(cls, window_id: UUID) -> Window:
        """Builds a new Window with a deterministic id."""

        payload = {"window_id": window_id}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Window):
            return value
        return Window.validate_invocation_value(value)

    async def add_layout(self, layout_id: UUID) -> WindowLayout:
        """Attaches a Layout to this Window."""

        payload = {"layout_id": layout_id}
        result = await invoke_instance(orm_model=self, function_name="add_layout", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.window.window_layout import WindowLayout

        if isinstance(value, WindowLayout):
            return value
        return WindowLayout.validate_invocation_value(value)

    async def set_active_layout(
        self, layout_id: UUID, mode: WindowActiveLayoutMode = WindowActiveLayoutMode.follow_thread_active
    ) -> None:
        """Sets the visible Attention Layout pointer for this Window without creating WindowLayout state."""

        payload = {"layout_id": layout_id, "mode": mode}
        await invoke_instance(orm_model=self, function_name="set_active_layout", payload=payload)
        return None


class WindowBuildInput(BaseModel):
    window_id: UUID


class WindowBuildOutput(BaseModel):
    value: Window


class WindowAddLayoutInput(BaseModel):
    layout_id: UUID


class WindowAddLayoutOutput(BaseModel):
    value: WindowLayout


class WindowSetActiveLayoutInput(BaseModel):
    layout_id: UUID
    mode: WindowActiveLayoutMode = Field(default=WindowActiveLayoutMode.follow_thread_active)


class WindowSetActiveLayoutOutput(BaseModel):
    pass


FUNCTIONS = {
    "Window": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Builds a new Window with a deterministic id.",
                "is_constructor": True,
            },
            "input": WindowBuildInput,
            "output": WindowBuildOutput,
        },
        "add_layout": {
            "canonical": {
                "name": "add_layout",
                "description": "Attaches a Layout to this Window.",
                "is_constructor": False,
            },
            "input": WindowAddLayoutInput,
            "output": WindowAddLayoutOutput,
        },
        "set_active_layout": {
            "canonical": {
                "name": "set_active_layout",
                "description": "Sets the visible Attention Layout pointer for this Window without creating WindowLayout state.",
                "is_constructor": False,
            },
            "input": WindowSetActiveLayoutInput,
            "output": WindowSetActiveLayoutOutput,
        },
    },
}

__all__ = [
    "Window",
    "WindowBuildInput",
    "WindowBuildOutput",
    "WindowAddLayoutInput",
    "WindowAddLayoutOutput",
    "WindowSetActiveLayoutInput",
    "WindowSetActiveLayoutOutput",
    "FUNCTIONS",
]
