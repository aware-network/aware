from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology Dto
from aware_interface_ontology_dto.render.pane_render_enums import PaneRenderCapabilityKind


class PaneRendererCapabilityRequirement(BaseModel):
    # Attributes
    capability_kind: PaneRenderCapabilityKind
    capability_key: str
    is_required: bool = Field(default=True)
