from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.session.attention_session_section import AttentionSessionSection


class AttentionLayoutTopologyTransitionSection(ORMModel):
    """
    Ordered active membership for one admitted section in one topology revision.
    Contract:
    - Parent constructor is AttentionLayoutTopologyTransition.
    - The section anchor is stable and remains under AttentionSessionLayout even
    when omitted from a later topology revision.
    """

    # Relationships
    attention_session_section: AttentionSessionSection | None = Field(default=None)

    # Attributes
    order: int

    # Foreign Keys
    attention_layout_topology_transition_id: UUID = Field(
        description="Foreign key for AttentionLayoutTopologyTransition.section_states"
    )
    attention_session_section_id: UUID = Field(
        description="Foreign key for AttentionLayoutTopologyTransitionSection.attention_session_section"
    )
