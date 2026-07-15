from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.layout.layout import Layout
    from aware_interface_ontology_dto.window.window_layout_section import WindowLayoutSection


class WindowLayout(BaseModel):
    """Window attachment/state for a canonical shareable Layout."""

    # Relationships
    layout: Layout | None = Field(default=None)
    layout_sections: list[WindowLayoutSection] = Field(default_factory=list)
