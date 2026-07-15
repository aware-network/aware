from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Interface Ontology Orm Models
from aware_interface_ontology_orm_models.window.window_enums import WindowActiveLayoutMode

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout import Layout
    from aware_interface_ontology_orm_models.window.window_layout import WindowLayout


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
