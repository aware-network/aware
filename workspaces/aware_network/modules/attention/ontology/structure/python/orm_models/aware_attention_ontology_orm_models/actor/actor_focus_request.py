from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Attention Ontology Orm Models
from aware_attention_ontology_orm_models.actor.actor_focus_enums import (
    ActorFocusLevelType,
    ActorFocusRequestStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.actor.actor_focus_request_response import ActorFocusRequestResponse
    from aware_attention_ontology_orm_models.focus.focus import Focus
    from aware_identity_ontology_orm_models.actor.actor import Actor


class ActorFocusRequest(ORMModel):
    """A focus request actor to actor"""

    # Relationships
    sender: Actor | None = Field(default=None, exclude=True)
    receiver: Actor | None = Field(default=None, exclude=True)
    focus: Focus | None = Field(default=None, exclude=True)
    response: ActorFocusRequestResponse | None = Field(default=None, exclude=True)

    # Attributes
    suggested_level: ActorFocusLevelType
    rationale: str
    status: ActorFocusRequestStatus = Field(default=ActorFocusRequestStatus.pending)
    confidence: float | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    response_message: str | None = Field(default=None)

    # Foreign Keys
    sender_id: UUID = Field(description="Foreign key for ActorFocusRequest.sender")
    receiver_id: UUID = Field(description="Foreign key for ActorFocusRequest.receiver")
    focus_id: UUID = Field(description="Foreign key for ActorFocusRequest.focus")
    response_id: UUID | None = Field(default=None, description="Foreign key for ActorFocusRequest.response")
