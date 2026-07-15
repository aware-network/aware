from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout_section import LayoutSection
    from aware_attention_ontology_orm_models.section.section import Section
    from aware_attention_ontology_orm_models.session.attention_focus_transition import AttentionFocusTransition


class AttentionSessionSection(ORMModel):
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

    # Foreign Keys
    attention_session_layout_id: UUID = Field(description="Foreign key for AttentionSessionLayout.sections")
    layout_section_id: UUID = Field(description="Foreign key for AttentionSessionSection.layout_section")
    section_id: UUID = Field(description="Foreign key for AttentionSessionSection.section")
    active_transition_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionSessionSection.active_transition"
    )
