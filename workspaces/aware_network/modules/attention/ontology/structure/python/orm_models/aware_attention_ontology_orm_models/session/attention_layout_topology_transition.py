from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.session.attention_layout_topology_transition_section import (
        AttentionLayoutTopologyTransitionSection,
    )


class AttentionLayoutTopologyTransition(ORMModel):
    """
    Immutable active-membership transition under one AttentionSessionLayout.
    Contract:
    - One transition is the atomic authority for the complete ordered set of
    active AttentionSessionSection anchors.
    - The active pointer lives on AttentionSessionLayout; history is immutable.
    - Omitted anchors are inactive for this revision, not deleted.
    """

    # Relationships
    previous_topology_transition: AttentionLayoutTopologyTransition | None = Field(default=None)
    section_states: list[AttentionLayoutTopologyTransitionSection] = Field(default_factory=list)

    # Attributes
    client_intent_id: str
    sequence: int = Field(default=0)
    transition_kind: str = Field(default="topology")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    attention_session_layout_id: UUID = Field(description="Foreign key for AttentionSessionLayout.topology_transitions")
    previous_topology_transition_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionLayoutTopologyTransition.previous_topology_transition"
    )
