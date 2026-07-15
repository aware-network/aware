from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.session.attention_session_section import AttentionSessionSection


class AttentionLayoutTransitionSection(BaseModel):
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
