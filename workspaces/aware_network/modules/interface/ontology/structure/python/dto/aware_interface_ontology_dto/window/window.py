from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology Dto
from aware_interface_ontology_dto.window.window_enums import WindowActiveLayoutMode

if TYPE_CHECKING:
    from aware_attention_ontology_dto.layout.layout import Layout
    from aware_interface_ontology_dto.window.window_layout import WindowLayout


class Window(BaseModel):
    """
    Window exposes Interface-owned visible layout state.
    Contract:
    - Environment/Thread owns shared active layout truth.
    - InterfaceWindow owns the protected thread target.
    - Window.active_layout is a direct visible Attention Layout pointer for replayable renderer state.
    - WindowLayout remains compatibility/override/cached section-binding state, not the normal selector.
    """

    # Relationships
    layouts: list[WindowLayout] = Field(default_factory=list)
    active_layout: Layout | None = Field(default=None)

    # Attributes
    window_id: UUID
    active_layout_mode: WindowActiveLayoutMode = Field(default=WindowActiveLayoutMode.follow_thread_active)
