from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology Dto
from aware_interface_ontology_dto.render.pane_render_enums import (
    PaneRenderNodeKind,
    PaneRenderSemanticRole,
)

if TYPE_CHECKING:
    from aware_interface_ontology_dto.render.pane_action_binding import PaneActionBinding
    from aware_interface_ontology_dto.render.pane_state_binding import PaneStateBinding
    from aware_interface_ontology_dto.render.pane_style_token_ref import PaneStyleTokenRef
    from aware_interface_ontology_dto.render.render_component_contract import RenderComponentContract


class PaneRenderNode(BaseModel):
    # Relationships
    state_bindings: list[PaneStateBinding] = Field(default_factory=list)
    action_bindings: list[PaneActionBinding] = Field(default_factory=list)
    style_tokens: list[PaneStyleTokenRef] = Field(default_factory=list)
    component_contract: RenderComponentContract | None = Field(default=None)

    # Attributes
    node_key: str
    parent_node_key: str | None = Field(default=None)
    node_kind: PaneRenderNodeKind
    semantic_role: PaneRenderSemanticRole | None = Field(default=None)
    slot_key: str | None = Field(default=None)
    order: int = Field(default=0)
    label: str | None = Field(default=None)
    text: str | None = Field(default=None)
    placeholder: str | None = Field(default=None)
    component_ref: str | None = Field(default=None)
    fallback_node_kind: PaneRenderNodeKind | None = Field(default=None)
    fallback_text: str | None = Field(default=None)
