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
from aware_attention_ontology_dto.actor.actor_focus_enums import (
    ActorFocusLevelType,
    ActorFocusRequestStatus,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.actor.actor_focus_request_response import ActorFocusRequestResponse
    from aware_attention_ontology_dto.focus.focus import Focus
    from aware_identity_ontology_dto.actor.actor import Actor


class ActorFocusRequest(BaseModel):
    """A focus request actor to actor"""

    # Relationships
    sender: Actor | None = Field(default=None)
    receiver: Actor | None = Field(default=None)
    focus: Focus | None = Field(default=None)
    response: ActorFocusRequestResponse | None = Field(default=None)

    # Attributes
    suggested_level: ActorFocusLevelType
    rationale: str
    status: ActorFocusRequestStatus = Field(default=ActorFocusRequestStatus.pending)
    confidence: float | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    response_message: str | None = Field(default=None)
