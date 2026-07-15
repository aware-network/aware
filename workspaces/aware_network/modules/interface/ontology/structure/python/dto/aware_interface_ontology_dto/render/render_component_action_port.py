from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology Dto
from aware_interface_ontology_dto.render.pane_render_enums import PaneActionEvent


class RenderComponentActionPort(BaseModel):
    # Attributes
    port_key: str
    event: PaneActionEvent = Field(default=PaneActionEvent.activate)
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)
