from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Interface Ontology Orm Models
from aware_interface_ontology_orm_models.render.pane_render_enums import (
    PaneRenderNodeKind,
    PaneRenderSemanticRole,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_interface_ontology_orm_models.render.pane_action_binding import PaneActionBinding
    from aware_interface_ontology_orm_models.render.pane_state_binding import PaneStateBinding
    from aware_interface_ontology_orm_models.render.pane_style_token_ref import PaneStyleTokenRef
    from aware_interface_ontology_orm_models.render.render_component_contract import RenderComponentContract


class PaneRenderNode(ORMModel):
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

    # Foreign Keys
    pane_render_spec_id: UUID = Field(description="Foreign key for PaneRenderSpec.nodes")
    component_contract_id: UUID | None = Field(
        default=None, description="Foreign key for PaneRenderNode.component_contract"
    )
