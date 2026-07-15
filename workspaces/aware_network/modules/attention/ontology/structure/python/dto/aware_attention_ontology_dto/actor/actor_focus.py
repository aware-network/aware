from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Attention Ontology Dto
from aware_attention_ontology_dto.actor.actor_focus_enums import ActorFocusLevelType

if TYPE_CHECKING:
    from aware_attention_ontology_dto.actor.actor_focus_evidence import ActorFocusEvidence
    from aware_attention_ontology_dto.focus.focus import Focus
    from aware_identity_ontology_dto.actor.actor import Actor


class ActorFocus(BaseModel):
    """Relationship Subject (Actor) -> Attention (Focus) -> Branch (Object)"""

    # Relationships
    actor: Actor | None = Field(default=None)
    focus: Focus | None = Field(default=None)
    evidences: list[ActorFocusEvidence] = Field(default_factory=list)

    # Attributes
    level: ActorFocusLevelType | None = Field(default=ActorFocusLevelType.medium)
    weight: float = Field(default=0.0)
    weight_algorithm: str | None = Field(default=None)
    weight_computed_at: datetime | None = Field(default=None)
    evidence_count: int = Field(default=0)
    last_evidence_at: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)
    last_accessed: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)
