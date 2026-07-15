from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.layout.layout_section import LayoutSection
    from aware_attention_ontology_dto.section.section import Section
    from aware_attention_ontology_dto.session.attention_focus_transition import AttentionFocusTransition


class AttentionSessionSection(BaseModel):
    """
    Session-local section state for Attention focus transitions.
    Contract:
    - Parent constructor is AttentionSessionLayout.
    - This row grounds transition history by LayoutSection -> Section.
    - Section.active_focus_scope remains legacy/global current state; replayable
    session focus truth is the transition list under this row.
    """

    # Relationships
    layout_section: LayoutSection | None = Field(default=None)
    section: Section | None = Field(default=None)
    transitions: list[AttentionFocusTransition] = Field(default_factory=list)
    active_transition: AttentionFocusTransition | None = Field(default=None)

    # Attributes
    section_key: str | None = Field(default=None)
    order: int = Field(default=0)
    is_active: bool = Field(default=True)
