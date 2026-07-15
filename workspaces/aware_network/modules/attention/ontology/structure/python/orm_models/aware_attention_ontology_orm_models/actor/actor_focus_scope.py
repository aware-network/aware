from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Attention Ontology Orm Models
from aware_attention_ontology_orm_models.actor.actor_focus_enums import ActorFocusLevelType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.actor.actor_focus_scope_evidence import ActorFocusScopeEvidence
    from aware_attention_ontology_orm_models.actor.actor_focus_scope_request import ActorFocusScopeRequest
    from aware_attention_ontology_orm_models.focus.focus_scope import FocusScope
    from aware_identity_ontology_orm_models.actor.actor import Actor


class ActorFocusScope(ORMModel):
    # Relationships
    actor: Actor | None = Field(default=None, exclude=True)
    focus_scope: FocusScope | None = Field(default=None, exclude=True)
    requests: list[ActorFocusScopeRequest] = Field(default_factory=list, exclude=True)
    evidences: list[ActorFocusScopeEvidence] = Field(default_factory=list, exclude=True)

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

    # Foreign Keys
    actor_id: UUID = Field(description="Foreign key for ActorFocusScope.actor")
    focus_scope_id: UUID = Field(description="Foreign key for ActorFocusScope.focus_scope")
