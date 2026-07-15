from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout import Layout
    from aware_interface_ontology_orm_models.window.window_layout_section import WindowLayoutSection


class WindowLayout(ORMModel):
    """Window attachment/state for a canonical shareable Layout."""

    # Relationships
    layout: Layout | None = Field(default=None, exclude=True)
    layout_sections: list[WindowLayoutSection] = Field(default_factory=list, exclude=True)

    # Foreign Keys
    window_id: UUID = Field(description="Foreign key for Window.layouts")
    layout_id: UUID = Field(description="Foreign key for WindowLayout.layout")
