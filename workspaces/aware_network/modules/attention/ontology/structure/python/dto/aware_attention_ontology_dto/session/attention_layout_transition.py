from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_attention_ontology_dto.session.attention_layout_topology_transition import (
        AttentionLayoutTopologyTransition,
    )
    from aware_attention_ontology_dto.session.attention_layout_transition_section import (
        AttentionLayoutTransitionSection,
    )


class AttentionLayoutTransition(BaseModel):
    """
    Immutable shared-layout transition under one AttentionSessionLayout.
    Contract:
    - One transition is the atomic authority for a complete mounted-section
    geometry vector.
    - The active pointer lives on AttentionSessionLayout; history is immutable.
    - Renderer pixels and mutable package defaults are not persisted here.
    """

    # Relationships
    previous_transition: AttentionLayoutTransition | None = Field(default=None)
    topology_transition: AttentionLayoutTopologyTransition | None = Field(default=None)
    section_states: list[AttentionLayoutTransitionSection] = Field(default_factory=list)

    # Attributes
    client_intent_id: str
    sequence: int = Field(default=0)
    transition_kind: str = Field(default="layout")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
