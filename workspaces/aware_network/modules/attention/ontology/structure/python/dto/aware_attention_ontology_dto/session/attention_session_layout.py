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
    from aware_attention_ontology_dto.layout.layout_config import LayoutConfig
    from aware_attention_ontology_dto.session.attention_layout_topology_transition import (
        AttentionLayoutTopologyTransition,
    )
    from aware_attention_ontology_dto.session.attention_layout_transition import AttentionLayoutTransition
    from aware_attention_ontology_dto.session.attention_session_section import AttentionSessionSection


class AttentionSessionLayout(BaseModel):
    """
    Session-local mounted Attention Layout.
    Contract:
    - Parent constructor is AttentionSession.
    - Layout/LayoutConfig remain Attention topology authorities.
    - Session layout state is local to AttentionSession.
    """

    # Relationships
    layout: Layout | None = Field(default=None)
    layout_config: LayoutConfig | None = Field(default=None)
    sections: list[AttentionSessionSection] = Field(default_factory=list)
    active_section: AttentionSessionSection | None = Field(default=None)
    topology_transitions: list[AttentionLayoutTopologyTransition] = Field(default_factory=list)
    active_topology_transition: AttentionLayoutTopologyTransition | None = Field(default=None)
    layout_transitions: list[AttentionLayoutTransition] = Field(default_factory=list)
    active_layout_transition: AttentionLayoutTransition | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)
    order: int = Field(default=0)
    is_active: bool = Field(default=True)
