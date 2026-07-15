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
    from aware_attention_ontology_orm_models.layout.layout_config import LayoutConfig
    from aware_attention_ontology_orm_models.session.attention_layout_topology_transition import (
        AttentionLayoutTopologyTransition,
    )
    from aware_attention_ontology_orm_models.session.attention_layout_transition import AttentionLayoutTransition
    from aware_attention_ontology_orm_models.session.attention_session_section import AttentionSessionSection


class AttentionSessionLayout(ORMModel):
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

    # Foreign Keys
    attention_session_id: UUID = Field(description="Foreign key for AttentionSession.layouts")
    layout_id: UUID = Field(description="Foreign key for AttentionSessionLayout.layout")
    layout_config_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionSessionLayout.layout_config"
    )
    active_section_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionSessionLayout.active_section"
    )
    active_topology_transition_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionSessionLayout.active_topology_transition"
    )
    active_layout_transition_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionSessionLayout.active_layout_transition"
    )
