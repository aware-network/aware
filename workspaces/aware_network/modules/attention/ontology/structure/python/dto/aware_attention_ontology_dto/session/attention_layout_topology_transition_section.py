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


class AttentionLayoutTopologyTransitionSection(BaseModel):
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
