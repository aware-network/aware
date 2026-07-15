from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor_role import ActorRole


class SessionMemberActorRole(BaseModel):
    """
    Existing Identity ActorRole evidence for one SessionMember.
    Contract:
    - Parent constructor is SessionMember.
    - References an existing ActorRole.
    - Does not grant, revoke, scope, or expire permission.
    """

    # Relationships
    actor_role: ActorRole | None = Field(default=None)

    # Attributes
    source_kind: str = Field(default="identity_session")
    status: str = Field(default="active")
    evidence_json: JsonObject | None = Field(default_factory=JsonObject)
