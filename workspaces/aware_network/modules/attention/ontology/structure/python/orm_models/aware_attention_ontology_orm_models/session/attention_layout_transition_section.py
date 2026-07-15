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


class AttentionLayoutTransitionSection(ORMModel):
    """
    Typed geometry state for one mounted section in one layout transition.
    Contract:
    - Parent constructor is AttentionLayoutTransition.
    - weight_micros is shared integer truth; active weights normalize exactly
    to 1_000_000 across the complete transition vector.
    - Hidden or collapsed sections have zero weight.
    """

    # Relationships
    attention_session_section: AttentionSessionSection | None = Field(default=None)

    # Attributes
    order: int
    weight_micros: int
    is_visible: bool = Field(default=True)
    is_collapsed: bool = Field(default=False)

    # Foreign Keys
    attention_layout_transition_id: UUID = Field(description="Foreign key for AttentionLayoutTransition.section_states")
    attention_session_section_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionLayoutTransitionSection.attention_session_section"
    )
