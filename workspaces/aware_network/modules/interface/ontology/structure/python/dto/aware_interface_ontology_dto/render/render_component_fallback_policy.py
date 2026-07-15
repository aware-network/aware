from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology Dto
from aware_interface_ontology_dto.render.pane_render_enums import PaneRenderNodeKind


class RenderComponentFallbackPolicy(BaseModel):
    # Attributes
    policy_key: str
    fallback_kind: str
    fallback_component_ref: str | None = Field(default=None)
    fallback_node_kind: PaneRenderNodeKind | None = Field(default=None)
    description: str | None = Field(default=None)
